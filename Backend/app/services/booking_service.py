from fastapi import HTTPException
from sqlmodel import Session

from app.models.booking import Booking
from app.repositories import booking_repository, property_repository
from app.schemas.booking import BookingCreate


def create_booking(session: Session, data: BookingCreate, guest_id: int) -> Booking:
    property = property_repository.get_by_id(session, data.property_id)
    if property is None or not property.is_active:
        raise HTTPException(status_code=404, detail="Property not found")

    overlapping = booking_repository.get_overlapping(
        session, data.property_id, data.check_in, data.check_out
    )
    if overlapping:
        raise HTTPException(status_code=409, detail="Property not available for those dates")

    nights = (data.check_out - data.check_in).days
    total_price = property.price_per_night * nights

    booking = Booking(
        property_id=data.property_id,
        guest_id=guest_id,
        check_in=data.check_in,
        check_out=data.check_out,
        total_price=total_price,
    )
    return booking_repository.create(session, booking)


def list_my_bookings(session: Session, guest_id: int) -> list[Booking]:
    return booking_repository.get_by_guest(session, guest_id)
