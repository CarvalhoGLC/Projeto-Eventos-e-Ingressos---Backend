from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend_events_tickets.core.database import Ticket, User, UserRole
from backend_events_tickets.core.auth import get_db, require_role
from backend_events_tickets.services import verify_qr_payload

router = APIRouter(prefix="/gate", tags=["Portaria"])


@router.post("/validate")
def validate_entry(
    qr_payload: str,
    gate_event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role([UserRole.GATE])),
):
    verification = verify_qr_payload(qr_payload)

    if not verification["valid"]:
        return {"status": "INVALID", "message": "🔴 QR Code alterado ou inválido!"}

    if verification["event_id"] != gate_event_id:
        return {"status": "WRONG_EVENT", "message": "🟠 Ingresso pertence a outro evento!"}

    ticket = db.query(Ticket).filter(Ticket.id == verification["ticket_id"]).first()

    if not ticket:
        return {"status": "INVALID", "message": "🔴 Ingresso não existe no sistema."}

    if ticket.is_validated:
        return {"status": "USED", "message": "🟠 ATENÇÃO: Ingresso já foi validado anteriormente!"}

    # Marca como validado para impedir dupla validação
    ticket.is_validated = True
    db.commit()

    return {"status": "VALID", "message": "🟢 Entrada Liberada!"}