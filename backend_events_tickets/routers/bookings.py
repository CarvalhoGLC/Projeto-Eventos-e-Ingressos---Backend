from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend_events_tickets.database import Ticket, User, UserRole
from backend_events_tickets.auth import get_db, require_role
from backend_events_tickets.schemas import BookingRequest
from backend_events_tickets.services import generate_signed_qr_payload, generate_share_token

router = APIRouter(tags=["Reservas e Ingressos"])


# --------------------- RESERVA E PAGAMENTO (CLIENTE) ---------------------
@router.post("/bookings")
def book_ticket(
    req: BookingRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role([UserRole.CLIENT])),
):
    # Simulação da cobrança
    if not req.simulate_payment_success:
        raise HTTPException(status_code=400, detail="Pagamento recusado pela operadora.")

    share_token = generate_share_token()
    ticket = Ticket(
        event_id=req.event_id,
        user_id=user.id,
        seat_number=req.seat_number,
        share_token=share_token,
    )

    try:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Este assento já foi vendido para este evento.",
        )

    # Geração do QR Code Infalsificável
    qr_payload = generate_signed_qr_payload(ticket.id, ticket.event_id)
    ticket.signature = qr_payload
    db.commit()

    return {
        "ticket_id": ticket.id,
        "seat": ticket.seat_number,
        "qr_code_payload": qr_payload,
        "share_link": f"/tickets/share/{share_token}",
    }


# --------------------- LINK COMPARTILHÁVEL DE INGRESSO ---------------------
@router.get("/tickets/share/{token}")
def get_shared_ticket(token: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.share_token == token).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ingresso compartilhado não encontrado.")
    return {
        "ticket_id": ticket.id,
        "event_id": ticket.event_id,
        "seat_number": ticket.seat_number,
        "qr_code_payload": ticket.signature,
    }