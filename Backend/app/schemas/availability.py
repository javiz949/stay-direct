from datetime import date

from sqlmodel import SQLModel


# Un rango ocupado. A propósito NO lleva guest_id ni el id de la reserva: este
# contrato es público y solo debe revelar QUÉ fechas están tomadas, nunca de quién.
class UnavailableRange(SQLModel):
    check_in: date
    check_out: date


class PropertyAvailability(SQLModel):
    property_id: int
    # Desde qué fecha se calculó; las estancias ya terminadas no se incluyen.
    since: date
    unavailable: list[UnavailableRange]
