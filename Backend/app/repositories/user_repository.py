from sqlmodel import Session, select

from app.models.user import User


def create(session: Session, user: User) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


def get_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)
