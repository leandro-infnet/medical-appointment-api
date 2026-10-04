"""Configuração local validada, sem chaves de assinatura padrão."""
import re
from functools import lru_cache
from pathlib import Path
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)
    jwt_secret: SecretStr
    jwt_issuer: str = "medical-appointment-api"
    jwt_audience: str = "clinic-human-clients"
    access_token_minutes: int = Field(default=15, ge=1, le=60)
    users_file: Path = Path(".local/usuarios.json")
    mfa_simulated_code: SecretStr
    agenda_cookie_secure: bool = True
    m2m_client_id: str = Field(default="laboratorio_parceiro", pattern=r"^[a-z0-9_]+$", max_length=64)
    m2m_client_secret_hash: SecretStr | None = None
    m2m_token_minutes: int = Field(default=5, ge=1, le=15)

    @field_validator("m2m_client_secret_hash", mode="before")
    @classmethod
    def hash_cliente(cls, value):
        if value == "":
            return None
        return value

    @field_validator("m2m_client_secret_hash")
    @classmethod
    def validar_hash_cliente(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and not re.fullmatch(r"\$2b\$(0[4-9]|1[0-4])\$[./A-Za-z0-9]{53}", value.get_secret_value()):
            raise ValueError("Credencial M2M deve ser hash bcrypt válido (custo 4 a 14).")
        return value

    @field_validator("jwt_secret")
    @classmethod
    def chave_forte(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value().encode()) < 32:
            raise ValueError("A chave JWT deve ter pelo menos 32 bytes.")
        return value

    @field_validator("mfa_simulated_code")
    @classmethod
    def codigo_simulado(cls, value: SecretStr) -> SecretStr:
        code = value.get_secret_value()
        if len(code) != 6 or not code.isascii() or not code.isdigit():
            raise ValueError("O código simulado deve ter seis dígitos ASCII.")
        return value

@lru_cache
def get_settings() -> Settings:
    # BaseSettings obtém os campos obrigatórios do ambiente, não de argumentos.
    return Settings()  # pyright: ignore[reportCallIssue]
