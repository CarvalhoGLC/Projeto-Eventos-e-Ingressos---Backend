from pydantic import BaseModel

from backend_events_tickets.database import UserRole


class UserRegister(BaseModel):
    email: str
    password: str
    role: UserRole


class EventCreate(BaseModel):
    title: str
    location: str
    date: str
    price: float


class BookingRequest(BaseModel):
    event_id: int
    seat_number: str
    simulate_payment_success: bool = True  # Simulação de pagamento