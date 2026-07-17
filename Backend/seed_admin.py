from sqlmodel import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import engine
from app.models.roles import Role
from app.models.user import User
from app.repositories import user_repository


def seed_admin() -> None:
    with Session(engine) as session:
        # Idempotente: si el admin ya existe, no hace nada. Se puede correr varias veces.
        if user_repository.get_by_email(session, settings.admin_email):
            print(f"Admin already exists: {settings.admin_email}")
            return

        admin = User(
            email=settings.admin_email,
            hashed_password=hash_password(settings.admin_password),
            role=Role.ADMIN,
        )
        user_repository.create(session, admin)
        print(f"Admin created: {settings.admin_email}")


if __name__ == "__main__":
    seed_admin()
