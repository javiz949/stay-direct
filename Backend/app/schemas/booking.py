from datetime import date, datetime
from decimal import Decimal

from pydantic import model_validator
from sqlmodel import SQLModel

from app.models.booking_status import BookingStatus


# El huésped solo manda propiedad y fechas. guest_id sale del token,
# total_price y status los pone el servidor.
class BookingCreate(SQLModel):
    property_id: int
    check_in: date
    check_out: date

    @model_validator(mode="after")
    def check_dates(self):
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be after check_in")
        if self.check_in < date.today():
            raise ValueError("check_in cannot be in the past")
        # Tope de noches: corta estancias absurdas antes de calcular el precio,
        # evitando el overflow de NUMERIC(10,2) que reventaría en un 500.
        if (self.check_out - self.check_in).days > 365:
            raise ValueError("stay cannot exceed 365 nights")
        return self


class BookingRead(SQLModel):
    id: int
    property_id: int
    guest_id: int
    check_in: date
    check_out: date
    total_price: Decimal
    status: BookingStatus
    created_at: datetime
