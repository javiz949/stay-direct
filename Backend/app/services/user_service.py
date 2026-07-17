from fastapi import HTTPException
from sqlmodel import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import UserCreate


def register_user(session: Session, data: UserCreate) -> User:
    if user_repository.get_by_email(session, data.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    # El rol lo fija el servidor, nunca el cliente: registro público siempre guest.
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        role="guest",
    )
    return user_repository.create(session, user)


def authenticate_user(session: Session, email: str, password: str) -> User:
    user = user_repository.get_by_email(session, email)
    # Mismo 401 para email inexistente y contraseña incorrecta: no revelar cuál falló.
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user
