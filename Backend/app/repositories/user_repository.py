from sqlmodel import Session, select

from app.models.user import User


def create(session: Session, user: User) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_by_email(session: Session, email: str) -> User | None:
    # Busca en minusculas: un correo = un usuario, sin importar como se escriba.
    return session.exec(select(User).where(User.email == email.lower())).first()


def get_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)
