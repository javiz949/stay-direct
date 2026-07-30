from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import require_guest
from app.db.session import get_session
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingRead
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


# Todo el módulo exige rol huésped: reservar, listar y cancelar son acciones del
# huésped. guest_id sale del token, nunca del body: reservas a tu nombre.
@router.post("", response_model=BookingRead, status_code=201)
def create_booking(
    data: BookingCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_guest),
):
    return booking_service.create_booking(session, data, guest_id=current_user.id)


@router.get("", response_model=list[BookingRead])
def list_my_bookings(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_guest),
):
    return booking_service.list_my_bookings(session, guest_id=current_user.id)


@router.post("/{booking_id}/cancel", response_model=BookingRead)
def cancel_booking(
    booking_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_guest),
):
    return booking_service.cancel_booking(session, booking_id, guest_id=current_user.id)
