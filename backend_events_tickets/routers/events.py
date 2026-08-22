from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend_events_tickets.core.database import Event, User, UserRole
from backend_events_tickets.core.auth import get_db, require_role
from backend_events_tickets.schemas import EventCreate, EventUpdate

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


def _get_owned_event_or_404(db: Session, event_id: int, user: User) -> Event:
    """Busca o evento e garante que pertence ao organizador logado."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    if event.organizer_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Você só pode gerenciar eventos que você mesmo criou.",
        )
    return event


@router.put("/{event_id}")
def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role([UserRole.ORGANIZER])),
):
    event = _get_owned_event_or_404(db, event_id, user)

    # exclude_unset: só aplica os campos que vieram no corpo da requisição
    update_data = event_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=204)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role([UserRole.ORGANIZER])),
):
    event = _get_owned_event_or_404(db, event_id, user)

    try:
        db.delete(event)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não é possível excluir um evento que já possui ingressos vendidos.",
        )

    return Response(status_code=204)