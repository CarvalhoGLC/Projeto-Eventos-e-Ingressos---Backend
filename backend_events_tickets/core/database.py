import enum
import os
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    create_engine,
    Integer,
    String,
    Float,
    Boolean,
    ForeignKey,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
    relationship,
)

# Caminho absoluto até o banco local. Sobe dois níveis (core/ -> backend_events_tickets/)
# para que o tickets_app.db continue no mesmo lugar de sempre.
BASE_DIR = Path(__file__).resolve().parent.parent  # core/ -> backend_events_tickets/

# Em ambientes serverless (Vercel, por exemplo) não existe disco persistente,
# então SQLite não funciona em produção. Se a variável DATABASE_URL estiver
# definida (ex.: uma connection string do Postgres), ela tem prioridade;
# sem ela, continua usando o tickets_app.db local — sem exigir nada extra
# para quem está rodando o projeto na própria máquina.
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'tickets_app.db'}"

# `check_same_thread` só existe/faz sentido para SQLite.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    ORGANIZER = "organizer"
    CLIENT = "client"
    GATE = "gate"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole))

    # Eventos organizados por este usuário (quando role == ORGANIZER)
    events_organized: Mapped[list["Event"]] = relationship(
        back_populates="organizer"
    )
    # Ingressos comprados por este usuário (quando role == CLIENT)
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="user")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    location: Mapped[Optional[str]] = mapped_column(String)
    date: Mapped[Optional[str]] = mapped_column(String)
    price: Mapped[Optional[float]] = mapped_column(Float)
    organizer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    organizer: Mapped["User"] = relationship(back_populates="events_organized")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="event")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    seat_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # ex: "A1"
    signature: Mapped[Optional[str]] = mapped_column(String, unique=True)  # Token HMAC assinado do QR Code
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False)  # Impede dupla validação
    share_token: Mapped[Optional[str]] = mapped_column(String, unique=True)  # Token para link compartilhável

    event: Mapped["Event"] = relationship(back_populates="tickets")
    user: Mapped["User"] = relationship(back_populates="tickets")

    # Impede que o mesmo lugar no mesmo evento seja reservado duas vezes
    __table_args__ = (
        UniqueConstraint("event_id", "seat_number", name="_event_seat_uc"),
    )