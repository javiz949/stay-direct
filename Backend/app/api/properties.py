from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.property import PropertyCreate, PropertyRead, PropertyUpdate
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


# PUT lleva el id en la ruta: edita una propiedad que ya existe.
@router.put("/{property_id}", response_model=PropertyRead)
def update_property(property_id: int, data: PropertyUpdate, session: Session = Depends(get_session)):
    return property_service.update_property(session, property_id, data)


# Borrado suave: devuelve la propiedad con is_active en false (no un 204 vacío).
@router.delete("/{property_id}", response_model=PropertyRead)
def delete_property(property_id: int, session: Session = Depends(get_session)):
    return property_service.delete_property(session, property_id)
