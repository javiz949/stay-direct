import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.config import settings
from app.db.session import get_session
from app.models.roles import Role
from app.models.user import User
from app.repositories import user_repository

# tokenUrl le dice a /docs dónde se consigue el token (habilita el botón Authorize).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub"))
    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = user_repository.get_by_id(session, user_id)
    # Inexistente o desactivado: el token no sirve para entrar.
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


# 403 (no 401): el usuario está autenticado, pero su rol no basta.
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
