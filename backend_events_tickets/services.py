import hmac
import hashlib
import uuid

import httpx

from backend_events_tickets.core.config import get_settings

settings = get_settings()


# 1. Busca externa no TMDb
async def search_tmdb_movies(query: str):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={settings.TMDB_API_KEY}&query={query}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()


# 2. Geração de código QR infalsificável (HMAC)
def generate_signed_qr_payload(ticket_id: int, event_id: int) -> str:
    raw_data = f"TICKET_ID={ticket_id}:EVENT_ID={event_id}"
    signature = hmac.new(
        settings.QR_SECRET.encode(), raw_data.encode(), hashlib.sha256
    ).hexdigest()
    return f"{raw_data}:SIG={signature}"


# 3. Validação da assinatura do QR Code
def verify_qr_payload(payload: str) -> dict:
    parts = payload.split(":SIG=")
    if len(parts) != 2:
        return {"valid": False}

    raw_data, received_sig = parts[0], parts[1]
    expected_sig = hmac.new(
        settings.QR_SECRET.encode(), raw_data.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, received_sig):
        return {"valid": False}

    # Extrai os IDs
    data_dict = dict(item.split("=") for item in raw_data.split(":"))
    return {
        "valid": True,
        "ticket_id": int(data_dict["TICKET_ID"]),
        "event_id": int(data_dict["EVENT_ID"]),
    }


def generate_share_token():
    return str(uuid.uuid4())