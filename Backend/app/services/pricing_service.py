from fastapi import HTTPException, status

from app.clients.ml_client import MLServiceUnavailable, ml_client
from app.schemas.pricing import PriceSuggestionRequest, PriceSuggestionResponse


def suggest_price(data: PriceSuggestionRequest) -> PriceSuggestionResponse:
    """Sugiere un precio por noche consultando el servicio de precios.

    El cliente reparte la petición entre las réplicas y hace failover, así que
    llegar aquí con error significa que NINGUNA réplica respondió.

    En ese caso se responde 503 en lugar de inventar una estimación: sugerir el
    precio es una comodidad, no un camino crítico —el administrador siempre puede
    capturarlo a mano—, y un número poco confiable que él podría dar por bueno es
    peor que admitir que el servicio no está disponible.
    """
    try:
        result = ml_client.predict_price(data.model_dump())
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
