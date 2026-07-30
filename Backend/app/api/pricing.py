from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.schemas.pricing import PriceSuggestionRequest, PriceSuggestionResponse
from app.services import pricing_service

router = APIRouter(prefix="/pricing", tags=["pricing"])


# Sugerir precio es una herramienta de administración del catálogo, no algo que
# necesite el huésped: va protegido por rol admin.
@router.post("/suggest", response_model=PriceSuggestionResponse, dependencies=[Depends(require_admin)])
def suggest_price(data: PriceSuggestionRequest):
    return pricing_service.suggest_price(data)


@router.get("/replicas", dependencies=[Depends(require_admin)])
def replicas_status():
    # Expone el estado de cada réplica del servicio de precios: qué réplicas están
    # en rotación, cuántos fallos acumulan y si responden.
    return pricing_service.replicas_status()
