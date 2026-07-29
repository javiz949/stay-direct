"""Entrena el modelo de precio y guarda el artefacto que consume la API.

Uso (desde MLService/):
    python -m app.train

Produce `artifacts/modelo_precio.joblib` con el modelo entrenado, el orden de las
columnas y las métricas de evaluación. La lógica de features vive en `features.py`
para que entrenamiento y predicción no se desincronicen.
"""

import ast
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from app import features

# El código vive en app/, pero los datos y artefactos están un nivel arriba.
ROOT = Path(__file__).parent.parent
DATASET = ROOT / "data" / "listings.csv.gz"
OUTPUT = ROOT / "artifacts" / "modelo_precio.joblib"

# Filtro de confianza: solo propiedades bien calificadas, con historial y activas.
# Las reseñas se usan SOLO para filtrar, nunca como features (una propiedad nueva
# no tiene reseñas).
MIN_RATING = 4.7
MIN_REVIEWS = 5

# Recorte de outliers de precio: quita errores de captura en ambas colas.
LOWER_CUT, UPPER_CUT = 0.01, 0.99

SEED = 42

HYPERPARAMS = {
    "max_iter": 800,
    "learning_rate": 0.03,
    "max_leaf_nodes": 63,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
}


def load_data() -> pd.DataFrame:
    """Lee el CSV crudo y aplica la limpieza. Devuelve datos listos para features."""
    raw = pd.read_csv(DATASET)

    columns = [
        "price", "room_type", "accommodates", "bedrooms", "bathrooms", "beds",
        "neighbourhood_cleansed", "latitude", "longitude", "amenities",
        "minimum_nights", "maximum_nights", "bathrooms_text",
        "review_scores_rating", "number_of_reviews", "number_of_reviews_ltm",
    ]
    data = raw[columns].copy()

    # price viene como texto: "$2,066.00"
    data["price"] = (data["price"].str.replace("$", "", regex=False)
                                  .str.replace(",", "", regex=False).astype(float))
    data = data.dropna(subset=["price"])
    print(f"  con precio:          {len(data)}")

    data = data[(data["review_scores_rating"] >= MIN_RATING) &
                (data["number_of_reviews"] >= MIN_REVIEWS) &
                (data["number_of_reviews_ltm"] > 0)]
    print(f"  tras filtro calidad: {len(data)}")

    lower, upper = data["price"].quantile([LOWER_CUT, UPPER_CUT])
    data = data[(data["price"] >= lower) & (data["price"] <= upper)]
    print(f"  tras recorte precio: {len(data)}  (rango {lower:.0f}-{upper:.0f})")

    # amenities viene como texto tipo lista: '["Wifi", "Kitchen"]'
    data["amenities"] = data["amenities"].apply(ast.literal_eval)

    return data.drop(columns=["review_scores_rating", "number_of_reviews", "number_of_reviews_ltm"])


def main() -> None:
    print("Cargando datos...")
    data = load_data()

    print("\nConstruyendo features...")
    X = features.build(data).astype(float)
    y = data["price"].reset_index(drop=True)
    print(f"  {X.shape[0]} filas x {X.shape[1]} features")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED)
    print(f"  entrenamiento: {len(X_train)} | prueba: {len(X_test)}")

    print("\nEntrenando HistGradientBoosting...")
    model = HistGradientBoostingRegressor(random_state=SEED, **HYPERPARAMS)
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    metrics = {
        "r2": float(r2_score(y_test, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        "mae": float(mean_absolute_error(y_test, pred)),
        "mape": float(np.mean(np.abs((y_test - pred) / y_test)) * 100),
    }
    print(f"\n  R2   {metrics['r2']:.4f}")
    print(f"  RMSE {metrics['rmse']:.0f} pesos")
    print(f"  MAE  {metrics['mae']:.0f} pesos")
    print(f"  MAPE {metrics['mape']:.1f} %")

    # Reentrenamos con TODOS los datos: el split era para medir, y al modelo que va
    # a producción conviene que aproveche también el 20% de prueba.
    print("\nReentrenando con el total para produccion...")
    final_model = HistGradientBoostingRegressor(random_state=SEED, **HYPERPARAMS)
    final_model.fit(X, y)

    artifact = {
        "model": final_model,
        "columns": list(X.columns),
        "metrics": metrics,
        "amenity_catalog": features.AMENITY_CATALOG,
        "trained_at": date.today().isoformat(),
        "n_samples": int(len(X)),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, OUTPUT, compress=3)
    size_mb = OUTPUT.stat().st_size / 1024 / 1024
    print(f"\nGuardado: {OUTPUT}  ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
