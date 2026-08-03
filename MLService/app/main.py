"""Microservicio de predicción de precio.

Corre como proceso independiente del backend principal. Su única responsabilidad
es recibir los datos de una propiedad y devolver un precio sugerido.

Uso:
    uvicorn app.main:app --port 8001
"""

from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, status

from app import features
from app.schemas import CatalogOut, HealthOut, PredictionOut, PropertyIn

ARTIFACT = Path(__file__).parent.parent / "artifacts" / "modelo_precio.joblib"

# El modelo se carga una vez al arrancar, no en cada petición: cargarlo toma
# cientos de milisegundos y no cambia entre llamadas.
state: dict = {"artifact": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if ARTIFACT.exists():
        state["artifact"] = joblib.load(ARTIFACT)
        metrics = state["artifact"]["metrics"]
        print(f"Model loaded: {len(state['artifact']['columns'])} features, R2 {metrics['r2']:.3f}")
    else:
        # No abortamos: el servicio arranca y responde /health en falso, para que el
        # backend sepa que debe usar su fallback en vez de esperar en vano.
        print(f"WARNING: artifact not found at {ARTIFACT}. Run: python -m app.train")
    yield
    state.clear()


app = FastAPI(
    title="Stay Direct - Price Service",
    description="Predice el precio por noche de una propiedad a partir de sus atributos.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    """Estado del servicio. El backend lo usa para decidir si intentar predecir."""
    artifact = state.get("artifact")
    if artifact is None:
        return HealthOut(status="degraded", model_loaded=False)
    return HealthOut(
        status="ok",
        model_loaded=True,
        model_trained_at=artifact["trained_at"],
        r2=round(artifact["metrics"]["r2"], 4),
        features=len(artifact["columns"]),
    )


@app.get("/catalog", response_model=CatalogOut)
def catalog() -> CatalogOut:
    """Valores que el modelo entiende. Evita que el backend los tenga hardcodeados."""
    return CatalogOut(
        amenities=features.AMENITY_CATALOG,
        room_types=features.ROOM_TYPES,
        neighborhoods=features.BOROUGHS,
    )


@app.post("/predict", response_model=PredictionOut)
def predict(property_in: PropertyIn) -> PredictionOut:
    """Devuelve el precio sugerido por noche para una propiedad."""
    artifact = state.get("artifact")
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not available",
        )

    if property_in.neighborhood not in features.BOROUGHS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown neighborhood: {property_in.neighborhood}",
        )
    if property_in.room_type not in features.ROOM_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown room_type: {property_in.room_type}",
        )

    # Coordenadas ausentes: se usa el centroide de la alcaldía. La alcaldía ya
    # se validó arriba, así que el acceso al catálogo es seguro.
    if property_in.latitude is None or property_in.longitude is None:
        property_in.latitude, property_in.longitude = features.CENTROIDS[property_in.neighborhood]

    row = pd.DataFrame([{
        "accommodates": property_in.accommodates,
        "bedrooms": property_in.bedrooms,
        "bathrooms": property_in.bathrooms,
        "beds": property_in.beds,
        "latitude": property_in.latitude,
        "longitude": property_in.longitude,
        "room_type": property_in.room_type,
        "neighbourhood_cleansed": property_in.neighborhood,
        "amenities": property_in.amenities,
        "minimum_nights": property_in.minimum_nights,
        "maximum_nights": property_in.maximum_nights,
        "bathrooms_text": property_in.bathroom_type,
    }])

    # reindex garantiza el mismo orden de columnas con que se entrenó: si llegan en
    # otro orden el modelo predice basura sin avisar.
    X = features.build(row).reindex(columns=artifact["columns"], fill_value=0).astype(float)
    price = float(artifact["model"].predict(X)[0])

    # El rango usa el MAE del modelo: es el error típico, así que comunica la
    # incertidumbre real en vez de dar un número solo.
    margin = artifact["metrics"]["mae"]

    return PredictionOut(
        suggested_price=round(price, 2),
        range_low=round(max(price - margin, 0), 2),
        range_high=round(price + margin, 2),
        model_trained_at=artifact["trained_at"],
    )
