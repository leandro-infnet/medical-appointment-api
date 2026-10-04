"""Configuração local validada, sem chaves de assinatura padrão."""
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
