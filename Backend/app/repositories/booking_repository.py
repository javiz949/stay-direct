from datetime import date

from sqlmodel import Session, select

from app.models.booking import Booking
from app.models.booking_status import BookingStatus


def create(session: Session, booking: Booking) -> Booking:
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def get_by_guest(session: Session, guest_id: int) -> list[Booking]:
    return list(session.exec(select(Booking).where(Booking.guest_id == guest_id)).all())


def get_by_id(session: Session, booking_id: int) -> Booking | None:
    return session.get(Booking, booking_id)


def update(session: Session, booking: Booking) -> Booking:
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def get_overlapping(session: Session, property_id: int, check_in: date, check_out: date) -> list[Booking]:
    # Dos rangos se solapan si uno empieza antes de que el otro termine y viceversa.
    # < y > estrictos: el día de salida se puede volver a reservar el mismo día.
    # Las canceladas no bloquean fechas.
    statement = select(Booking).where(
        Booking.property_id == property_id,
        Booking.status != BookingStatus.CANCELLED,
        Booking.check_in < check_out,
        Booking.check_out > check_in,
    )
    return list(session.exec(statement).all())
