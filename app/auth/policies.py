"""Negação por padrão com papel, vínculo confiável e propriedade do recurso."""
from fastapi import HTTPException
from app.auth.dependencies import UsuarioDep
from app.database.identidades import VINCULOS
from app.database.consultas import obter_consulta_por_id
from app.models.consultas import Consulta
from app.models.identidades import Papel, Usuario

def exigir_papel(usuario: Usuario, papel: Papel) -> None:
    if usuario.papel != papel:
        raise HTTPException(403, "Operação não permitida para este papel.")

def profissional(usuario: UsuarioDep) -> Usuario:
    exigir_papel(usuario, Papel.PROFISSIONAL)
    return usuario

def pode_acessar(usuario: Usuario, paciente_id: int, profissional_id: int) -> bool:
    return (usuario.papel == Papel.PROFISSIONAL and usuario.profissional_id == profissional_id
            and (paciente_id, profissional_id) in VINCULOS)

def exigir_vinculo(usuario: Usuario, paciente_id: int, profissional_id: int) -> None:
    if not pode_acessar(usuario, paciente_id, profissional_id):
        raise HTTPException(403, "Vínculo não autorizado.")


def consulta_autorizada(consulta_id: int, usuario: Usuario) -> Consulta:
    consulta = obter_consulta_por_id(consulta_id)
    if consulta is None or not pode_acessar(usuario, consulta.paciente_id, consulta.profissional_id):
        raise HTTPException(404, "Consulta não encontrada.")
    return consulta
