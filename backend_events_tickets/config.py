from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Caminho absoluto até o .env, independente de onde o comando é executado
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """
    Configurações da aplicação, carregadas automaticamente do arquivo .env
    ou de variáveis de ambiente do sistema.

    Se SECRET_KEY não estiver definida, a aplicação falha ao iniciar
    com um erro claro — evitando rodar em produção com valores inválidos.
    """

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8
    TMDB_API_KEY: str
    QR_SECRET: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Retorna a instância única (cacheada) das configurações.

    O type: ignore abaixo é necessário porque o Pylance não sabe que
    o Pydantic Settings preenche os campos automaticamente a partir
    do .env / variáveis de ambiente em tempo de execução.
    """
    return Settings()  # type: ignore[call-arg]