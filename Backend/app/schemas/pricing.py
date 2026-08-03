from sqlmodel import Field, SQLModel


# Contrato de entrada: lo que el administrador captura al publicar. Habla el
# idioma de la plataforma (alcaldía, amenidades en español); traducirlo al
# contrato del servicio de precios es trabajo del service, no del cliente.
class PriceSuggestionRequest(SQLModel):
    accommodates: int = Field(ge=1, le=20)
    bedrooms: float = Field(ge=0, le=20)
    bathrooms: float = Field(ge=0, le=20)

    # Alcaldía de CDMX. Las coordenadas no se piden: el servicio de precios usa
    # el centroide de la alcaldía, del que es dueño.
    neighborhood: str

    # Nombres del catálogo propio (en español). El service traduce las que el
    # modelo conoce y descarta el resto.
    amenities: list[str] = []

    # Opcional: el admin no captura camas hoy; si falta, el service la aproxima.
    beds: float | None = Field(default=None, ge=1, le=30)


# Contrato de salida. `served_by` deja ver qué réplica atendió: sirve para
# verificar el balanceo. Si ninguna réplica responde, la API devuelve 503 en vez
# de un precio.
class PriceSuggestionResponse(SQLModel):
    suggested_price: float
    range_low: float
    range_high: float
    served_by: str | None = None
