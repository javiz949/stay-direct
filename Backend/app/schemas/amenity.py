from sqlmodel import SQLModel


# Contrato de salida de una amenidad: cómo se ve cada una al leer una propiedad.
class AmenityRead(SQLModel):
    id: int
    name: str
