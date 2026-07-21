from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from app.models.roles import Role


class UserCreate(SQLModel):
    email: EmailStr
    # max_length=72: bcrypt no acepta mas de 72 bytes y lanzaria un 500;
    # aqui se corta con un 422 antes de llegar al hasheo.
    password: str = Field(min_length=8, max_length=72)


# Sin password ni hashed_password: la contraseña nunca sale por HTTP.
class UserRead(SQLModel):
    id: int
    email: EmailStr
    role: Role
    is_active: bool
    created_at: datetime


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
