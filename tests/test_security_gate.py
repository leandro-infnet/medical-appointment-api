"""A política bloqueia riscos e falhas de análise sem resultados verdes fictícios."""
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from scripts.security_gate import RelatorioInvalido, avaliar_bandit, avaliar_sca, avaliar_pytest, executar


def bandit(severity=None):
    results = [] if severity is None else [{"test_id": "B999", "issue_severity": severity, "issue_confidence": "LOW"}]
    return {"results": results, "errors": [], "metrics": {"_totals": {"loc": 10}}}


def sca(vulns=None):
    return {"dependencies": [{"name": "pacote-ficticio", "version": "1.0", "vulns": vulns or []}]}


@pytest.mark.parametrize("severity,blocked", [(None, False), ("LOW", False), ("MEDIUM", False), ("HIGH", True)])
def test_bandit_limiar_nativo_sem_inventar_cvss(severity, blocked):
    assert bool(avaliar_bandit(bandit(severity), int(severity is not None))) is blocked


@pytest.mark.parametrize("report,exit_code", [({}, 0), (bandit(), 2), (bandit("HIGH"), 0),
    ({**bandit(), "errors": [{"reason": "arquivo não lido"}]}, 0),
    ({**bandit(), "metrics": {"_totals": {"loc": 0}}}, 0), (bandit("UNKNOWN"), 1)])
def test_bandit_incompleto_ou_exit_incompativel_bloqueia(report, exit_code):
    with pytest.raises(RelatorioInvalido):
        avaliar_bandit(report, exit_code)


def test_sca_sem_score_nao_e_classificada_como_baixa():
    assert avaliar_sca(sca(), 0) == []
    assert avaliar_sca(sca([{"id": "CVE-FICTICIA", "fix_versions": []}]), 1)


@pytest.mark.parametrize("report,exit_code", [({}, 0), ({"dependencies": []}, 0), (sca(), 1),
    ({"dependencies": [{"name": "pacote", "skip_reason": "não analisado"}]}, 0),
    (sca([{}]), 1)])
def test_sca_sem_cobertura_ou_classificacao_valida_bloqueia(report, exit_code):
    with pytest.raises(RelatorioInvalido):
        avaliar_sca(report, exit_code)


@pytest.mark.parametrize("failures,errors,skipped,exit_code", [(0, 0, 0, 0), (1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 0), (0, 0, 0, 2)])
def test_pytest_falha_erro_skip_e_exit_code(tmp_path, failures, errors, skipped, exit_code):
    path = tmp_path / "pytest.xml"
    path.write_text(f'<testsuites><testsuite tests="1" failures="{failures}" errors="{errors}" skipped="{skipped}"/></testsuites>')
    assert bool(avaliar_pytest(path, exit_code)) is bool(failures or errors or skipped or exit_code)


def test_pytest_sem_testes_nao_aprova(tmp_path):
    path = tmp_path / "pytest.xml"
    path.write_text('<testsuites><testsuite tests="0"/></testsuites>')
    with pytest.raises(RelatorioInvalido):
        avaliar_pytest(path, 0)


@pytest.mark.parametrize("cenario", ["aprovar", "high", "ausente", "invalido", "scanner_falhou"])
def test_runner_real_exit_e_persistencia_de_relatorios(tmp_path, cenario):
    def command(args, **kwargs):
        from subprocess import CompletedProcess
        if "pytest" in args:
            Path(next(arg.split("=", 1)[1] for arg in args if arg.startswith("--junitxml="))).write_text(
                '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"/></testsuites>')
            return CompletedProcess(args, 0)
        destino = Path(args[-1])
        if "bandit" in args:
            severity = "HIGH" if cenario == "high" else None
            destino.write_text(json.dumps(bandit(severity)))
            return CompletedProcess(args, int(severity is not None))
        if cenario == "ausente":
            return CompletedProcess(args, 0)
        if cenario == "invalido":
            destino.write_text("{")
            return CompletedProcess(args, 0)
        destino.write_text(json.dumps(sca()))
        return CompletedProcess(args, 2 if cenario == "scanner_falhou" else 0)
    # Um relatório antigo válido não pode aprovar execução sem relatório novo.
    (tmp_path / "sca.json").write_text(json.dumps(sca()))
    with patch("scripts.security_gate.subprocess.run", side_effect=command):
        code = executar(tmp_path)
    assert code == int(cenario != "aprovar")
    resultado = json.loads((tmp_path / "gate.json").read_text())
    assert resultado["aprovado"] is (cenario == "aprovar")
    assert (tmp_path / "pytest.log").exists()
    assert (tmp_path / "bandit.log").exists()


def test_sca_exclui_so_projeto_editavel_com_demais_pacotes_analisados():
    report = sca()
    report["dependencies"].append({"name": "medical-appointment-api", "skip_reason": "distribution marked as editable"})
    assert avaliar_sca(report, 0) == []
    report["dependencies"].pop(0)
    with pytest.raises(RelatorioInvalido):
        avaliar_sca(report, 0)
