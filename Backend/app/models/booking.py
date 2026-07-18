from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Column, DateTime, String
from sqlmodel import Field, SQLModel

from app.models.booking_status import BookingStatus


class Booking(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # Llaves foráneas: conectan la reserva con la propiedad y el huésped.
    # index porque se consulta seguido por propiedad (disponibilidad) y por huésped (sus reservas).
    property_id: int = Field(foreign_key="property.id", index=True)
    guest_id: int = Field(foreign_key="user.id", index=True)
    # date y no datetime: la reserva es por noches; la hora de entrada/salida
    # es una política de la propiedad, no un dato de cada reserva.
    check_in: date
    check_out: date
    # Lo calcula el backend (noches x precio), nunca el cliente.
    total_price: Decimal = Field(max_digits=10, decimal_places=2)
    status: BookingStatus = Field(
        default=BookingStatus.PENDING,
        sa_column=Column(String, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
