from datetime import datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel


# Sin table=True: no es una tabla, es el contrato de datos que valida la API.
# Campos que el cliente sí manda (todos menos id y created_at).
class PropertyBase(SQLModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1)
    city: str = Field(min_length=1)
    neighborhood: str = Field(min_length=1)
    address: str = Field(min_length=1)
    property_type: str = Field(min_length=1)

    max_guests: int = Field(gt=0, le=50)
    bedrooms: int = Field(ge=0)
    bathrooms: float = Field(gt=0)
    price_per_night: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    is_active: bool = True


# Lo que entra al crear. Vacía por ahora: hereda todo de la base. Existe para
# alojar campos que solo apliquen al crear, sin ensuciar el contrato común.
class PropertyCreate(PropertyBase):
    pass


# Lo que sale al responder. id es int (no int | None): al devolverla ya lo tiene.
class PropertyRead(PropertyBase):
    id: int
    created_at: datetime
