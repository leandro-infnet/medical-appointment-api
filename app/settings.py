"""Configuração local validada, sem chaves de assinatura padrão."""
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit
from pydantic import Field, SecretStr, field_validator, model_validator
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
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    login_rate_limit: int = Field(default=5, ge=1, le=10000)
    general_rate_limit: int = Field(default=60, ge=1, le=10000)

    @model_validator(mode="after")
    def limite_credenciais_mais_restritivo(self):
        if self.login_rate_limit >= self.general_rate_limit:
            raise ValueError("A cota de credenciais deve ser menor que a cota geral.")
        return self

    @field_validator("cors_origins")
    @classmethod
    def origens_explicitas(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("Informe pelo menos uma origem CORS explícita.")
        for origin in value:
            parsed = urlsplit(origin)
            if (origin != origin.strip() or "*" in origin or parsed.scheme not in ("http", "https")
                    or not parsed.hostname or parsed.username is not None or parsed.password is not None
                    or parsed.path or parsed.query or parsed.fragment):
                raise ValueError("Origem deve conter somente esquema HTTP(S), host e porta opcional.")
            _ = parsed.port  # Verifica porta numérica e faixa, sem alterar a origem.
        return value

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
