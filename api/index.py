"""
Ponto de entrada usado pelo Vercel para servir a aplicação FastAPI.

O runtime Python do Vercel (@vercel/python) detecta automaticamente uma
variável chamada `app` que seja uma aplicação ASGI/WSGI neste arquivo —
não precisa de nenhum adaptador (Mangum, etc.) para FastAPI.
"""

from backend_events_tickets.main import app  # noqa: F401