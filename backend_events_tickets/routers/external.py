from fastapi import APIRouter

from backend_events_tickets.services import search_tmdb_movies

router = APIRouter(prefix="/external", tags=["Busca Externa"])


@router.get("/movies")
async def external_movies(query: str):
    return await search_tmdb_movies(query)