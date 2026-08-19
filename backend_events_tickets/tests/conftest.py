import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Garante variáveis de ambiente ANTES de importar a aplicação, já que
# Settings() (config.py) exige esses campos no momento da inicialização.
os.environ.setdefault("SECRET_KEY", "test_secret_key_apenas_para_testes")
os.environ.setdefault("TMDB_API_KEY", "test_tmdb_key")
os.environ.setdefault("QR_SECRET", "test_qr_secret_apenas_para_testes")

from backend_events_tickets.main import app  # noqa: E402
from backend_events_tickets.database import Base  # noqa: E402
from backend_events_tickets.auth import get_db  # noqa: E402

# Banco de dados isolado para os testes — nunca toca no tickets_app.db real
TEST_DB_PATH = Path(__file__).resolve().parent / "test_tickets_app.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Cria as tabelas antes da suíte e apaga o arquivo de teste ao final."""
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture()
def client():
    return TestClient(app)


def _unique_email(role: str) -> str:
    return f"{role}_{uuid.uuid4().hex[:8]}@example.com"


def register_and_login(client: TestClient, role: str, password: str = "senha123") -> str:
    """Registra um usuário com o papel informado, faz login e retorna o access_token."""
    email = _unique_email(role)
    client.post("/register", json={"email": email, "password": password, "role": role})
    response = client.post("/token", data={"username": email, "password": password})
    return response.json()["access_token"]


@pytest.fixture()
def auth_headers(client):
    """Fixture-fábrica: auth_headers("organizer") -> {"Authorization": "Bearer ..."}"""

    def _make(role: str) -> dict:
        token = register_and_login(client, role)
        return {"Authorization": f"Bearer {token}"}

    return _make