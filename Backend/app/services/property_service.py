from fastapi import HTTPException
from sqlmodel import Session

from app.models.property import Property
from app.repositories import property_repository
from app.schemas.property import PropertyCreate, PropertyUpdate


def create_property(session: Session, data: PropertyCreate) -> Property:
    # Traduce el schema de entrada al model que persiste el repo.
    property = Property(**data.model_dump())
    return property_repository.create(session, property)


def list_properties(session: Session) -> list[Property]:
    return property_repository.get_all(session)


def get_property(session: Session, property_id: int) -> Property:
    property = property_repository.get_by_id(session, property_id)
    # El repo reporta el None; la decisión de que eso es un 404 es del service.
    if property is None:
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
