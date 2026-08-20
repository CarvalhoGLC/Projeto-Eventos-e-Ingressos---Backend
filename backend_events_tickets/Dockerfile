# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Evita a criação de .pyc e força os logs a saírem sem buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Instala as dependências primeiro (aproveita o cache de camadas do Docker
# — só reinstala se o requirements.txt mudar, não a cada alteração de código)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY backend_events_tickets ./backend_events_tickets

# Usuário não-root, por segurança
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Em produção usamos uvicorn diretamente (o `fastapi dev` é só para
# desenvolvimento local, com reload automático).
CMD ["uvicorn", "backend_events_tickets.main:app", "--host", "0.0.0.0", "--port", "8000"]