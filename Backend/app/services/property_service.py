from fastapi import HTTPException
from sqlmodel import Session

from app.models.property import Property
from app.repositories import property_repository
from app.schemas.property import PropertyCreate


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
