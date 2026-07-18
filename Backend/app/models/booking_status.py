from enum import Enum


# Hereda de str para guardarse como valor ("pending"), y limita los estados
# posibles a esta lista cerrada.
class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
