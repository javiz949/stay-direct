from datetime import date

from sqlalchemy import text
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


def get_active_by_property(session: Session, property_id: int, since: date) -> list[Booking]:
    """Reservas vigentes de una propiedad, para calcular su disponibilidad.

    Solo desde `since` hacia adelante: las estancias ya terminadas no sirven para
    elegir fechas futuras y solo harían más grande la respuesta.
    """
    statement = select(Booking).where(
        Booking.property_id == property_id,
        Booking.status != BookingStatus.CANCELLED,
        Booking.check_out > since,
    )
    return list(session.exec(statement).all())


def lock_property(session: Session, property_id: int) -> None:
    """Toma un candado exclusivo sobre las reservas de una propiedad.

    Si otra transaccion ya lo tiene, esta espera hasta que aquella termine. El
    candado se libera solo al cerrar la transaccion, con commit o con rollback,
    asi que no hay forma de dejarlo colgado.

    Hace falta porque entre consultar el traslape y guardar la reserva hay una
    ventana en la que dos peticiones simultaneas pasan ambas el chequeo: ninguna
    ve a la otra porque todavia no esta guardada.

    El candado es por property_id, asi que reservas de propiedades distintas no
    se estorban entre si; solo se forman en fila las que compiten por la misma.
    """
    # Parametro vinculado, no interpolacion de string: el id nunca se concatena
    # al SQL.
    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": property_id})


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
