from datetime import datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel

from app.schemas.amenity import AmenityRead


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


# Lo que entra al crear: la base más las amenidades, por id. Van como ids y no
# como nombres porque el catálogo ya existe en la DB y el id es su referencia
# estable (el nombre podría corregirse sin romper nada).
class PropertyCreate(PropertyBase):
    amenity_ids: list[int] = []


# Lo que sale al responder. id es int (no int | None): al devolverla ya lo tiene.
class PropertyRead(PropertyBase):
    id: int
    created_at: datetime
    # Lista de amenidades de la propiedad (viene del M2M). [] si no tiene.
    amenities: list[AmenityRead] = []


# Edición parcial: todos los campos opcionales. Si un campo no viene, no se toca;
# si viene, se aplica su validación (un precio presente igual debe ser > 0).
class PropertyUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1)
    city: str | None = Field(default=None, min_length=1)
    neighborhood: str | None = Field(default=None, min_length=1)
    address: str | None = Field(default=None, min_length=1)
    property_type: str | None = Field(default=None, min_length=1)
    max_guests: int | None = Field(default=None, gt=0, le=50)
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: float | None = Field(default=None, gt=0)
    price_per_night: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    is_active: bool | None = None
