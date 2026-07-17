from enum import Enum


# Hereda de str para que se guarde y viaje como texto ("guest"/"admin"),
# pero como Enum limita los valores posibles a esta lista cerrada.
class Role(str, Enum):
    GUEST = "guest"
    ADMIN = "admin"
