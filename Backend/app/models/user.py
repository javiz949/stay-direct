from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlmodel import Field, SQLModel

from app.models.roles import Role


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # index porque cada login busca al usuario por email.
    email: str = Field(unique=True, index=True)
    hashed_password: str
    # Columna String (no enum nativo): al heredar Role de str se guarda el valor
    # ("guest"), y el Enum valida en Python los roles permitidos.
    role: Role = Field(default=Role.GUEST, sa_column=Column(String, nullable=False))
    is_active: bool = True
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
