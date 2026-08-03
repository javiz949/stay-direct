from sqlmodel import Session, select

from app.models.amenity import Amenity


def get_all(session: Session) -> list[Amenity]:
    return list(session.exec(select(Amenity)).all())


def get_by_ids(session: Session, amenity_ids: list[int]) -> list[Amenity]:
    # Devuelve solo las que existen; el service compara longitudes para detectar
    # ids inválidos y decidir el error HTTP (el repo no sabe de HTTP).
    if not amenity_ids:
        return []
    statement = select(Amenity).where(Amenity.id.in_(amenity_ids))  # type: ignore[union-attr]
    return list(session.exec(statement).all())
