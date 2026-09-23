"""Configurações e fixtures para a suíte de testes com pytest."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.memoria import reset_banco


@pytest.fixture(autouse=True)
def isolar_banco_dados():
    """Garante que o estado do armazenamento seja resetado antes de cada teste."""
    reset_banco()
    yield
    reset_banco()


@pytest.fixture
def client():
    """Fixture que provê um cliente de testes HTTP para a aplicação."""
    with TestClient(app) as test_client:
        yield test_client
