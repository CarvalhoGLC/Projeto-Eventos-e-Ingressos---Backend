from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend_events_tickets.database import Base, engine, User
from backend_events_tickets.auth import get_db, pwd_context, create_access_token
from backend_events_tickets.schemas import UserRegister
from backend_events_tickets.routers import events, bookings, external, gate

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Eventos e Ingressos")

app.include_router(events.router)
app.include_router(bookings.router)
app.include_router(external.router)
app.include_router(gate.router)


# --------------------- REGISTRO E AUTH ---------------------
@app.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    hashed = pwd_context.hash(data.password)
    user = User(email=data.email, hashed_password=hashed, role=data.role)

    try:
        db.add(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado.")

    return {"message": "Usuário criado com sucesso"}


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}