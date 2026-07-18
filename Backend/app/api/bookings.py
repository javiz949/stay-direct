from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingRead
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


# guest_id sale del token (current_user), nunca del body: reservas a tu nombre.
@router.post("", response_model=BookingRead, status_code=201)
def create_booking(
    data: BookingCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return booking_service.create_booking(session, data, guest_id=current_user.id)


@router.get("", response_model=list[BookingRead])
def list_my_bookings(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return booking_service.list_my_bookings(session, guest_id=current_user.id)
