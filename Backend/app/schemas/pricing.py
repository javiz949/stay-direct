from sqlmodel import Field, SQLModel


# Contrato de entrada: lo que el administrador captura de la propiedad.
class PriceSuggestionRequest(SQLModel):
    accommodates: int = Field(ge=1, le=20)
    bedrooms: float = Field(ge=0, le=20)
    bathrooms: float = Field(ge=0, le=20)
    beds: float = Field(ge=0, le=30)

    # Rango de la Ciudad de México: el modelo solo aprendió de este mercado.
    latitude: float = Field(ge=19.0, le=19.9)
    longitude: float = Field(ge=-99.4, le=-98.9)

    room_type: str
    neighborhood: str

    amenities: list[str] = []
    minimum_nights: int = Field(default=1, ge=1, le=365)
    maximum_nights: int = Field(default=365, ge=1, le=1125)
    bathroom_type: str = "private"


# Contrato de salida. `served_by` deja ver qué réplica atendió: sirve para
# verificar el balanceo. Si ninguna réplica responde, la API devuelve 503 en vez
# de un precio.
class PriceSuggestionResponse(SQLModel):
    suggested_price: float
    range_low: float
    range_high: float
    served_by: str | None = None
