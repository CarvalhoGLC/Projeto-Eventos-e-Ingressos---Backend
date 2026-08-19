from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend_events_tickets.database import Event, User, UserRole
from backend_events_tickets.auth import get_db, require_role
from backend_events_tickets.schemas import EventCreate

router = APIRouter(prefix="/events", tags=["Eventos"])


@router.post("")
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role([UserRole.ORGANIZER])),
):
    event = Event(**event_data.model_dump(), organizer_id=user.id)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event