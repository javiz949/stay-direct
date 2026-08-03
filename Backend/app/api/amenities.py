from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.repositories import amenity_repository
from app.schemas.amenity import AmenityRead

router = APIRouter(prefix="/amenities", tags=["amenities"])


# Público, como el resto de las lecturas del catálogo: los nombres de las
# amenidades ya viajan dentro de cada propiedad.
@router.get("", response_model=list[AmenityRead])
def list_amenities(session: Session = Depends(get_session)):
    return amenity_repository.get_all(session)
