from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

# Solo para el analizador (Pylance): en runtime TYPE_CHECKING es False, así que
# este import NO corre y no hay import circular con property.py.
if TYPE_CHECKING:
    from app.models.property import Property


# Tabla puente del muchos-a-muchos: cada fila conecta una propiedad con una amenidad.
# Las dos FKs juntas son la llave primaria, así que un par (propiedad, amenidad) no se repite.
class PropertyAmenity(SQLModel, table=True):
    property_id: int | None = Field(default=None, foreign_key="property.id", primary_key=True)
    amenity_id: int | None = Field(default=None, foreign_key="amenity.id", primary_key=True)


class Amenity(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # unique: "wifi" no se repite en el catálogo de amenidades.
    name: str = Field(unique=True, index=True)
    # Lado inverso del M2M: desde una amenidad, sus propiedades (a través del puente).
    properties: list["Property"] = Relationship(back_populates="amenities", link_model=PropertyAmenity)
