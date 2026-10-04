"""Contas confiáveis e contratos públicos de autenticação."""
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

class Papel(StrEnum):
    PROFISSIONAL = "profissional"
    RECEPCAO = "recepcionista"
    ADMIN = "administrador"

class Usuario(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    username: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")
    papel: Papel
    senha_hash: SecretStr
    profissional_id: int | None = Field(default=None, gt=0)
    ativo: bool = True

    @model_validator(mode="after")
    def vinculo_profissional(self):
        if (self.papel == Papel.PROFISSIONAL) != (self.profissional_id is not None):
            raise ValueError("Somente conta profissional deve ter profissional_id.")
        return self

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class MFAChallengeResponse(BaseModel):
    challenge_id: str
    expires_in: int = 300
    detail: str = "Segundo fator simulado necessário."

class MFAInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    challenge_id: str = Field(min_length=1, max_length=128)
    code: SecretStr = Field(min_length=6, max_length=6)
