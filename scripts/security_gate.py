"""Executa verificações obrigatórias e bloqueia relatórios inválidos ou riscos definidos."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from tempfile import gettempdir
from defusedxml.common import DefusedXmlException
from defusedxml import ElementTree

ROOT = Path(__file__).resolve().parents[1]
PYTEST_REPORT = "pytest.xml"
BANDIT_REPORT = "bandit.json"
SCA_REPORT = "sca.json"


class RelatorioInvalido(ValueError):
    """Análise ausente/incompleta não é ausência de vulnerabilidades."""


def avaliar_bandit(report: dict, exit_code: int | None) -> list[str]:
    resultados = report.get("results")
    metricas = report.get("metrics", {}).get("_totals", {})
    if (not isinstance(resultados, list) or report.get("errors") != []
            or metricas.get("loc", 0) <= 0 or exit_code != int(bool(resultados))):
        raise RelatorioInvalido("Bandit não concluiu uma análise válida.")
    motivos = []
    for finding in resultados:
        if (not isinstance(finding, dict) or finding.get("issue_severity") not in {"LOW", "MEDIUM", "HIGH"}
                or finding.get("issue_confidence") not in {"LOW", "MEDIUM", "HIGH"}
                or not finding.get("test_id")):
            raise RelatorioInvalido("Finding Bandit sem classificação válida.")
        if finding["issue_severity"] == "HIGH":
            motivos.append("Bandit HIGH: " + finding["test_id"])
    return motivos


def avaliar_sca(report: dict, exit_code: int | None) -> list[str]:
    dependencies = report.get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise RelatorioInvalido("SCA sem dependências analisadas.")
    motivos = []
    analisadas = 0
    for dependency in dependencies:
        if (isinstance(dependency, dict) and dependency.get("name") == "medical-appointment-api"
                and dependency.get("skip_reason") == "distribution marked as editable"):
            # A aplicação editável é verificada pelo SAST/pytest; SCA cobre pacotes instalados.
            continue
        motivos.extend(avaliar_dependencia_sca(dependency))
        analisadas += 1
    if analisadas == 0:
        raise RelatorioInvalido("SCA não analisou nenhum pacote instalado.")
    if exit_code != int(bool(motivos)):
        raise RelatorioInvalido("Exit code SCA incompatível com o relatório.")
    return sorted(set(motivos))


def avaliar_dependencia_sca(dependency: dict) -> list[str]:
    if (not isinstance(dependency, dict) or dependency.get("skip_reason")
            or not dependency.get("name") or not dependency.get("version")
            or not isinstance(dependency.get("vulns"), list)):
        raise RelatorioInvalido("SCA incompleta ou dependência não analisada.")
    motivos = []
    for vulnerability in dependency["vulns"]:
        if not isinstance(vulnerability, dict) or not vulnerability.get("id"):
            raise RelatorioInvalido("SCA com vulnerabilidade sem identificador.")
        motivos.append("SCA pendente de correção/triagem: " + vulnerability["id"])
    return motivos


def avaliar_pytest(path: Path, exit_code: int | None) -> list[str]:
    root = ElementTree.parse(path).getroot()
    if root is None:
        raise RelatorioInvalido("Relatório pytest sem elemento raiz.")
    suites = list(root.iter("testsuite"))
    if not suites or sum(int(suite.get("tests", "0")) for suite in suites) <= 0:
        raise RelatorioInvalido("pytest sem testes executados.")
    if any(int(suite.get("skipped", "0")) for suite in suites):
        return ["Teste obrigatório pulado."]
    if exit_code != 0 or any(int(suite.get(key, "0")) for suite in suites for key in ("failures", "errors")):
        return ["Teste obrigatório falhou."]
    return []


def executar(output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    # Remove apenas os relatórios desta execução, para não aceitar resultados antigos.
    for name in (PYTEST_REPORT, BANDIT_REPORT, SCA_REPORT):
        (output / name).unlink(missing_ok=True)
    comandos = {
        "pytest": [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short", "--junitxml=" + str(output / PYTEST_REPORT)],
        "bandit": [sys.executable, "-m", "bandit", "-r", "app", "scripts", "--ignore-nosec", "-f", "json", "-o", str(output / BANDIT_REPORT)],
        "sca": [sys.executable, "-m", "pip_audit", "--skip-editable", "--cache-dir", str(Path(gettempdir()) / "at-ex12-audit-cache"), "--progress-spinner", "off", "-f", "json", "-o", str(output / SCA_REPORT)],
    }
    statuses = {}
    motivos = []
    for name, command in comandos.items():
        try:
            with (output / (name + ".log")).open("w") as log:
                result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=300, check=False)
            statuses[name] = result.returncode
        except (OSError, subprocess.TimeoutExpired):
            statuses[name] = None
            motivos.append("Falha operacional: " + name)
    validadores = {
        "pytest": lambda: avaliar_pytest(output / PYTEST_REPORT, statuses["pytest"]),
        "bandit": lambda: avaliar_bandit(json.loads((output / BANDIT_REPORT).read_text()), statuses["bandit"]),
        "sca": lambda: avaliar_sca(json.loads((output / SCA_REPORT).read_text()), statuses["sca"]),
    }
    for name, validate in validadores.items():
        try:
            motivos.extend(validate())
        except (OSError, ValueError, TypeError, AttributeError, ElementTree.ParseError, DefusedXmlException) as error:
            motivos.append("Relatório inválido/ausente: " + name + " (" + type(error).__name__ + ")")
    resultado = {"aprovado": not motivos, "exit_codes": statuses, "motivos": motivos}
    (output / "gate.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return int(bool(motivos))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="pytest + SAST + SCA com decisão verificável.")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "security")
    args = parser.parse_args()
    raise SystemExit(executar(args.output.resolve()))
