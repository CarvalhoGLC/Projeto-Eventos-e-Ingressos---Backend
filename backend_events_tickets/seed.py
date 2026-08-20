"""
Script de seed: popula o banco com dados de teste para permitir explorar
o fluxo completo (organizador, clientes, portaria, evento e ingresso) sem
precisar cadastrar tudo manualmente.

Uso (de dentro da pasta backend/, com o ambiente virtual ativado):

    python -m backend_events_tickets.seed

É seguro rodar mais de uma vez — o script verifica o que já existe antes
de criar, então não duplica usuários/eventos/ingressos.
"""

from backend_events_tickets.core.database import (
    Base,
    engine,
    SessionLocal,
    User,
    UserRole,
    Event,
    Ticket,
)
from backend_events_tickets.core.auth import pwd_context
from backend_events_tickets.services import generate_signed_qr_payload, generate_share_token

SEED_PASSWORD = "senha123"


def get_or_create_user(db, email: str, role: UserRole) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(email=email, hashed_password=pwd_context.hash(SEED_PASSWORD), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_event(db, organizer: User) -> Event:
    event = db.query(Event).filter(Event.title == "Show de Lançamento").first()
    if event:
        return event
    event = Event(
        title="Show de Lançamento",
        location="Arena Central",
        date="2026-12-15",
        price=120.0,
        organizer_id=organizer.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_or_create_ticket(db, event: Event, client: User) -> Ticket:
    ticket = (
        db.query(Ticket)
        .filter(Ticket.event_id == event.id, Ticket.seat_number == "A1")
        .first()
    )
    if ticket:
        return ticket

    ticket = Ticket(
        event_id=event.id,
        user_id=client.id,
        seat_number="A1",
        share_token=generate_share_token(),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    ticket.signature = generate_signed_qr_payload(ticket.id, ticket.event_id)
    db.commit()
    db.refresh(ticket)
    return ticket


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        organizer = get_or_create_user(db, "organizador@example.com", UserRole.ORGANIZER)
        client1 = get_or_create_user(db, "cliente1@example.com", UserRole.CLIENT)
        client2 = get_or_create_user(db, "cliente2@example.com", UserRole.CLIENT)
        get_or_create_user(db, "portaria@example.com", UserRole.GATE)

        event = get_or_create_event(db, organizer)
        ticket = get_or_create_ticket(db, event, client1)

        print("\nSeed concluído. Credenciais (senha igual para todos):\n")
        print(f"  Organizador : organizador@example.com  |  senha: {SEED_PASSWORD}")
        print(f"  Cliente 1   : cliente1@example.com      |  senha: {SEED_PASSWORD}  (já tem o assento A1)")
        print(f"  Cliente 2   : cliente2@example.com      |  senha: {SEED_PASSWORD}  (sem ingresso — pode reservar)")
        print(f"  Portaria    : portaria@example.com      |  senha: {SEED_PASSWORD}")
        print(f"\n  Evento      : id={event.id} — \"{event.title}\"")
        print(f"  Ticket A1   : id={ticket.id}")
        print(f"  QR payload  : {ticket.signature}")
        print(f"  Link        : /tickets/share/{ticket.share_token}\n")
    finally:
        db.close()


if __name__ == "__main__":
    run()