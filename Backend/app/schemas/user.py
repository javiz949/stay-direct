from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class UserCreate(SQLModel):
    email: EmailStr
    password: str = Field(min_length=8)


# Sin password ni hashed_password: la contraseña nunca sale por HTTP.
class UserRead(SQLModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
