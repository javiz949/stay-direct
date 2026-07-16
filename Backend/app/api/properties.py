from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.property import PropertyCreate, PropertyRead
from app.services import property_service

router = APIRouter(prefix="/properties", tags=["properties"])


# response_model=PropertyRead traduce el model a schema en la salida y documenta
# la respuesta en /docs. 201 porque una creación no es un 200 genérico.
@router.post("", response_model=PropertyRead, status_code=201)
def create_property(data: PropertyCreate, session: Session = Depends(get_session)):
    return property_service.create_property(session, data)


@router.get("", response_model=list[PropertyRead])
def list_properties(session: Session = Depends(get_session)):
    return property_service.list_properties(session)


@router.get("/{property_id}", response_model=PropertyRead)
def get_property(property_id: int, session: Session = Depends(get_session)):
    return property_service.get_property(session, property_id)
