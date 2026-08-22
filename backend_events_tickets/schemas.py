from typing import Optional

from pydantic import BaseModel

from backend_events_tickets.core.database import UserRole


class UserRegister(BaseModel):
    email: str
    password: str
    role: UserRole


class EventCreate(BaseModel):
    title: str
    location: str
    date: str
    price: float


class EventUpdate(BaseModel):
    """Todos os campos são opcionais — só atualiza o que for enviado."""
    title: Optional[str] = None
    location: Optional[str] = None
    date: Optional[str] = None
    price: Optional[float] = None


class BookingRequest(BaseModel):
    event_id: int
    seat_number: str
    simulate_payment_success: bool = True  # Simulação de pagamento