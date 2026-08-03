from fastapi import HTTPException, status

from app.clients.ml_client import MLBadRequest, MLServiceUnavailable, ml_client
from app.schemas.pricing import PriceSuggestionRequest, PriceSuggestionResponse

# El catálogo propio está en español; el modelo aprendió con los nombres de
# Airbnb en inglés. Solo se traducen las que el modelo conoce: las demás
# (alberca, gimnasio, aire acondicionado...) no entraron a su top de amenidades
# discriminantes, así que no aportan señal y se descartan sin error.
AMENITY_TRANSLATIONS = {
    "Wifi": "Wifi",
    "Cocina": "Kitchen",
    "Agua caliente": "Hot water",
    "Refrigerador": "Refrigerator",
    "Área de trabajo": "Dedicated workspace",
    "TV con streaming": "TV",
    "Detector de humo": "Smoke alarm",
}

# La plataforma renta unidades completas (delimitación del proyecto), así que el
# room_type del modelo es constante: no se le pregunta al admin algo que siempre
# tendría la misma respuesta.
ROOM_TYPE = "Entire home/apt"


def suggest_price(data: PriceSuggestionRequest) -> PriceSuggestionResponse:
    """Sugiere un precio por noche consultando el servicio de precios.

    Este service traduce del idioma de la plataforma al contrato del modelo:
    amenidades ES->EN, room_type fijo y camas aproximadas si no vienen. El
    cliente reparte la petición entre las réplicas y hace failover, así que
    llegar aquí con error significa que NINGUNA réplica respondió.

    En ese caso se responde 503 en lugar de inventar una estimación: sugerir el
    precio es una comodidad, no un camino crítico —el administrador siempre puede
    capturarlo a mano—, y un número poco confiable que él podría dar por bueno es
    peor que admitir que el servicio no está disponible.
    """
    payload = {
        "accommodates": data.accommodates,
        "bedrooms": data.bedrooms,
        "bathrooms": data.bathrooms,
        # Aproximación mientras la plataforma no capture camas: al menos una,
        # y una por recámara como piso.
        "beds": data.beds if data.beds is not None else max(1.0, data.bedrooms),
        "neighborhood": data.neighborhood,
        "room_type": ROOM_TYPE,
        "amenities": [
            AMENITY_TRANSLATIONS[a] for a in data.amenities if a in AMENITY_TRANSLATIONS
        ],
    }

    try:
        result = ml_client.predict_price(payload)
    except MLBadRequest as exc:
        # El servicio está sano; los datos capturados no. Se propaga el motivo
        # para que el admin pueda corregir, en vez de un 503 engañoso.
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    except MLServiceUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Price service unavailable, set the price manually",
        )

    return PriceSuggestionResponse(
        suggested_price=result["suggested_price"],
        range_low=result["range_low"],
        range_high=result["range_high"],
        served_by=result.get("served_by"),
    )


def replicas_status() -> list[dict]:
    """Estado de las réplicas. Útil para monitoreo y para demostrar el balanceo."""
    return ml_client.health()
