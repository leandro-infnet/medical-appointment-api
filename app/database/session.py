"""Engine local e sessão por requisição, sem conexão ou sessão global."""
import sqlite3
from pathlib import Path
from typing import Annotated, Iterator
from fastapi import Depends, Request
from sqlalchemy import event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel, create_engine
from app.models.tabelas import PacienteTabela, ProfissionalTabela


class BancoIndisponivel(Exception):
    """SQLite ocupado além do timeout; não equivale a consulta inexistente."""


def criar_engine(database_url: str) -> Engine:
    url = make_url(database_url)
    Path(str(url.database)).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 5}, echo=False)

    @event.listens_for(engine, "connect")
    def configurar_sqlite(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def inicializar_banco(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")
        for id_, nome, email in [(1, "Douglas Heffernan", "douglas@sitcom.com"),
                                 (2, "Arthur Spooner", "arthur@sitcom.com")]:
            if session.get(PacienteTabela, id_) is None:
                session.add(PacienteTabela(id=id_, nome=nome, email=email))
        for id_, nome, especialidade, crm in [
            (1, "Dr. Carrie Heffernan", "Cardiologia", "12345-SP"),
            (2, "Dr. Kelly Palmer", "Ortopedia", "67890-SP"),
        ]:
            if session.get(ProfissionalTabela, id_) is None:
                session.add(ProfissionalTabela(id=id_, nome=nome, especialidade=especialidade, crm=crm))
        session.commit()


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        try:
            if request.method in {"POST", "PATCH", "DELETE"} and request.url.path.rstrip("/").startswith("/consultas"):
                # Reserva a escrita antes da leitura de ownership e de conflitos.
                session.connection().exec_driver_sql("BEGIN IMMEDIATE")
            yield session
        except OperationalError as error:
            session.rollback()
            code = getattr(error.orig, "sqlite_errorcode", None)
            if code is not None and code & 0xFF in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}:
                raise BancoIndisponivel() from error
            raise
        except Exception:
            session.rollback()
            raise


SessionDep = Annotated[Session, Depends(get_session)]
