"""Contratos de la API: qué recibe y qué devuelve el servicio.

Validar aquí es importante: el modelo predice basura en silencio si le llegan
datos fuera de rango, así que preferimos rechazar la petición con un 422.
"""

from pydantic import BaseModel, Field

from app.features import BOROUGHS, ROOM_TYPES


class PropertyIn(BaseModel):
    """Datos de una propiedad tal como los captura el administrador al publicar."""

    accommodates: int = Field(ge=1, le=20, description="Capacidad máxima de huéspedes")
    bedrooms: float = Field(ge=0, le=20, description="Número de recámaras")
    bathrooms: float = Field(ge=0, le=20, description="Número de baños")
    beds: float = Field(ge=0, le=30, description="Número de camas")

    # Límites aproximados de la Ciudad de México: el modelo solo aprendió de CDMX,
    # así que una coordenada de otra ciudad daría una predicción sin sentido.
    latitude: float = Field(ge=19.0, le=19.9)
    longitude: float = Field(ge=-99.4, le=-98.9)

    room_type: str = Field(description=f"Uno de: {ROOM_TYPES}")
    neighborhood: str = Field(description="Alcaldía de CDMX")

    amenities: list[str] = Field(default_factory=list, description="Amenidades del catálogo")

    minimum_nights: int = Field(default=1, ge=1, le=365)
    maximum_nights: int = Field(default=365, ge=1, le=1125)
    bathroom_type: str = Field(default="private", description="private, shared o half")

    model_config = {
        "json_schema_extra": {
            "example": {
                "accommodates": 4,
                "bedrooms": 2,
                "bathrooms": 1,
                "beds": 2,
                "latitude": 19.4110,
                "longitude": -99.1710,
                "room_type": "Entire home/apt",
                "neighborhood": "Cuauhtémoc",
                "amenities": ["Wifi", "Kitchen", "Hot water", "Elevator"],
                "minimum_nights": 2,
                "maximum_nights": 30,
                "bathroom_type": "private",
            }
        }
    }


class PredictionOut(BaseModel):
    """Precio sugerido más el contexto para interpretarlo."""

    suggested_price: float = Field(description="Precio por noche estimado, en pesos")
    range_low: float = Field(description="Extremo inferior del rango sugerido")
    range_high: float = Field(description="Extremo superior del rango sugerido")
    model_trained_at: str = Field(description="Fecha de entrenamiento del modelo")


class HealthOut(BaseModel):
    """Estado del servicio. El backend lo consulta para saber si vale la pena llamar."""

    status: str
    model_loaded: bool
    model_trained_at: str | None = None
    r2: float | None = None
    features: int | None = None


class CatalogOut(BaseModel):
    """Valores válidos, para que el backend arme su formulario sin adivinar."""

    amenities: list[str]
    room_types: list[str]
    neighborhoods: list[str]
