"""Entrena el modelo de precio y guarda el artefacto que consume el microservicio.

Uso (desde Backend/):
    python -m app.ml.train

Produce `app/ml/artifacts/modelo_precio.joblib` con el modelo entrenado, el orden
de las columnas y las métricas de evaluación. La lógica de features vive en
`features.py` para que entrenamiento y predicción no se desincronicen.
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

from app.ml import features

AQUI = Path(__file__).parent
DATOS = AQUI / "data" / "listings.csv.gz"
SALIDA = AQUI / "artifacts" / "modelo_precio.joblib"

# Filtro de confianza: solo propiedades bien calificadas, con historial y activas.
# Las reseñas se usan SOLO para filtrar, nunca como features (una propiedad nueva
# no tiene reseñas).
RATING_MIN = 4.7
MIN_RESENAS = 5

# Recorte de outliers de precio: quita errores de captura en ambas colas.
CORTE_BAJO, CORTE_ALTO = 0.01, 0.99

SEMILLA = 42

HIPERPARAMETROS = {
    "max_iter": 800,
    "learning_rate": 0.03,
    "max_leaf_nodes": 63,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
}


def cargar_datos() -> pd.DataFrame:
    """Lee el CSV crudo y aplica la limpieza. Devuelve datos listos para features."""
    df = pd.read_csv(DATOS)

    columnas = [
        "price", "room_type", "accommodates", "bedrooms", "bathrooms", "beds",
        "neighbourhood_cleansed", "latitude", "longitude", "amenities",
        "minimum_nights", "maximum_nights", "bathrooms_text",
        "review_scores_rating", "number_of_reviews", "number_of_reviews_ltm",
    ]
    d = df[columnas].copy()

    # price viene como texto: "$2,066.00"
    d["price"] = (d["price"].str.replace("$", "", regex=False)
                            .str.replace(",", "", regex=False).astype(float))
    d = d.dropna(subset=["price"])
    print(f"  con precio:          {len(d)}")

    d = d[(d["review_scores_rating"] >= RATING_MIN) &
          (d["number_of_reviews"] >= MIN_RESENAS) &
          (d["number_of_reviews_ltm"] > 0)]
    print(f"  tras filtro calidad: {len(d)}")

    bajo, alto = d["price"].quantile([CORTE_BAJO, CORTE_ALTO])
    d = d[(d["price"] >= bajo) & (d["price"] <= alto)]
    print(f"  tras recorte precio: {len(d)}  (rango {bajo:.0f}-{alto:.0f})")

    # amenities viene como texto tipo lista: '["Wifi", "Kitchen"]'
    d["amenities"] = d["amenities"].apply(ast.literal_eval)

    return d.drop(columns=["review_scores_rating", "number_of_reviews", "number_of_reviews_ltm"])


def main() -> None:
    print("Cargando datos...")
    datos = cargar_datos()

    print("\nConstruyendo features...")
    X = features.construir(datos).astype(float)
    y = datos["price"].reset_index(drop=True)
    print(f"  {X.shape[0]} filas x {X.shape[1]} features")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEMILLA)
    print(f"  entrenamiento: {len(X_train)} | prueba: {len(X_test)}")

    print("\nEntrenando HistGradientBoosting...")
    modelo = HistGradientBoostingRegressor(random_state=SEMILLA, **HIPERPARAMETROS)
    modelo.fit(X_train, y_train)

    pred = modelo.predict(X_test)
    metricas = {
        "r2": float(r2_score(y_test, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        "mae": float(mean_absolute_error(y_test, pred)),
        "mape": float(np.mean(np.abs((y_test - pred) / y_test)) * 100),
    }
    print(f"\n  R2   {metricas['r2']:.4f}")
    print(f"  RMSE {metricas['rmse']:.0f} pesos")
    print(f"  MAE  {metricas['mae']:.0f} pesos")
    print(f"  MAPE {metricas['mape']:.1f} %")

    # Reentrenamos con TODOS los datos: el split era para medir, y el modelo que
    # va a producción conviene que aproveche también el 20% de prueba.
    print("\nReentrenando con el total para produccion...")
    modelo_final = HistGradientBoostingRegressor(random_state=SEMILLA, **HIPERPARAMETROS)
    modelo_final.fit(X, y)

    artefacto = {
        "modelo": modelo_final,
        "columnas": list(X.columns),
        "metricas": metricas,
        "catalogo_amenidades": features.CATALOGO_AMENIDADES,
        "entrenado": date.today().isoformat(),
        "n_muestras": int(len(X)),
    }

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artefacto, SALIDA, compress=3)
    mb = SALIDA.stat().st_size / 1024 / 1024
    print(f"\nGuardado: {SALIDA}  ({mb:.2f} MB)")


if __name__ == "__main__":
    main()
