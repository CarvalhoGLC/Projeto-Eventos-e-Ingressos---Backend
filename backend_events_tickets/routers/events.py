from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend_events_tickets.core.database import Event, User, UserRole
from backend_events_tickets.core.auth import get_db, require_role
from backend_events_tickets.schemas import EventCreate

router = APIRouter(prefix="/events", tags=["Eventos"])


@router.get("")
def list_events(db: Session = Depends(get_db)):
    return db.query(Event).all()


@router.get("/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    return event


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