from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.core.security import create_access_token
from app.db.session import get_session
from app.schemas.user import Token, UserCreate, UserRead
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(data: UserCreate, session: Session = Depends(get_session)):
    return user_service.register_user(session, data)


# OAuth2PasswordRequestForm trae los campos username/password: username lleva el email.
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = user_service.authenticate_user(session, form_data.username, form_data.password)
    token = create_access_token(subject=str(user.id), role=user.role)
    return Token(access_token=token)
