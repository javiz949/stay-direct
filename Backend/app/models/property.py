from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models.amenity import Amenity, PropertyAmenity


class Property(SQLModel, table=True):
    # int | None: antes de guardar, Postgres aún no asignó el id.
    id: int | None = Field(default=None, primary_key=True)

    title: str
    description: str
    city: str
    neighborhood: str
    address: str
    # Texto libre por ahora; restringir a Enum al definir los schemas.
    property_type: str

    max_guests: int
    bedrooms: int
    bathrooms: float
    # Decimal y no float: float no representa dinero con exactitud (0.1 + 0.2).
    price_per_night: Decimal = Field(max_digits=10, decimal_places=2)

    # Borrado suave: al "eliminar" se pone en False; borrar la fila rompería
    # las reservas que la referencian.
    is_active: bool = True

    # sa_column fuerza TIMESTAMPTZ: sin él SQLModel genera un timestamp sin
    # zona horaria y se pierde el UTC. Al tomar la columna a mano, el
    # nullable=False también corre por nuestra cuenta.
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    # Amenidades (muchos-a-muchos vía la tabla puente): property.amenities da la lista.
    amenities: list["Amenity"] = Relationship(back_populates="properties", link_model=PropertyAmenity)
