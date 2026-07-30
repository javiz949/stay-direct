from datetime import date

from fastapi import HTTPException
from sqlmodel import Session

from app.models.property import Property
from app.repositories import booking_repository, property_repository
from app.schemas.availability import PropertyAvailability, UnavailableRange
from app.schemas.property import PropertyCreate, PropertyUpdate


def create_property(session: Session, data: PropertyCreate) -> Property:
    # Traduce el schema de entrada al model que persiste el repo.
    property = Property(**data.model_dump())
    return property_repository.create(session, property)


def list_properties(session: Session) -> list[Property]:
    return property_repository.get_all(session)


def get_property(session: Session, property_id: int) -> Property:
    property = property_repository.get_by_id(session, property_id)
    # Inexistente o con borrado suave: para la API "no existe" -> 404.
    if property is None or not property.is_active:
        raise HTTPException(status_code=404, detail="Property not found")
    return property


def update_property(session: Session, property_id: int, data: PropertyUpdate) -> Property:
    # Reusa get_property: si no existe, lanza el 404 aquí mismo.
    property = get_property(session, property_id)
    # exclude_unset: solo los campos que el cliente realmente mandó (edición parcial).
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(property, key, value)
    return property_repository.update(session, property)


def delete_property(session: Session, property_id: int) -> Property:
    # Borrado suave: no se elimina la fila, se desactiva. Reusa el mismo update.
    property = get_property(session, property_id)
    property.is_active = False
    return property_repository.update(session, property)


def get_availability(session: Session, property_id: int) -> PropertyAvailability:
    """Fechas ocupadas de una propiedad, para que el cliente no ofrezca días que
    van a ser rechazados.

    Devuelve solo rangos de fechas: nunca el huésped ni el id de la reserva. Es
    información pública, así que no debe revelar quién se hospeda dónde.
    """
    # Reusa get_property: si no existe o está desactivada, lanza el 404.
    get_property(session, property_id)

    today = date.today()
    bookings = booking_repository.get_active_by_property(session, property_id, since=today)

    return PropertyAvailability(
        property_id=property_id,
        since=today,
        unavailable=[
            UnavailableRange(check_in=b.check_in, check_out=b.check_out) for b in bookings
        ],
    )
