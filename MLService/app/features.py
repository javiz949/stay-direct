"""Construcción de features del modelo de precio.

Este módulo es la ÚNICA fuente de verdad de las features: lo importan tanto el
entrenamiento (`train.py`) como la API de predicción (`main.py`). Si la lógica
viviera duplicada en los dos lados, se desincronizarían y el modelo recibiría
features distintas al entrenar y al predecir (training-serving skew).

Las constantes geográficas y el catálogo de amenidades están congelados aquí a
propósito: en tiempo de ejecución no se necesita el CSV ni el geojson, solo
aritmética sobre las coordenadas.
"""

import numpy as np
import pandas as pd

# Las 40 amenidades más frecuentes del mercado de CDMX. Es también el catálogo que
# debe ofrecer el formulario del backend, para que entrenamiento y producción
# coincidan. Se probaron 14/25/40/60/80: 40 fue el óptimo; más allá, las
# amenidades poco frecuentes meten ruido y el desempeño baja.
AMENITY_CATALOG = [
    "Hot water", "Kitchen", "Hangers", "Wifi", "Dishes and silverware",
    "Cooking basics", "Carbon monoxide alarm", "Iron", "Bed linens", "Microwave",
    "Essentials", "Dedicated workspace", "Hair dryer", "Shampoo", "Smoke alarm",
    "Self check-in", "Long term stays allowed", "Refrigerator",
    "Room-darkening shades", "Extra pillows and blankets", "Dining table",
    "Blender", "TV", "Body soap", "Freezer", "First aid kit", "Cleaning products",
    "Coffee", "Exterior security cameras on property", "Wine glasses",
    "Fire extinguisher", "Luggage dropoff allowed", "Shower gel", "Coffee maker",
    "Portable fans", "Elevator", "Laundromat nearby", "Oven", "Private entrance",
    "Toaster",
]

# Centroide (lat, lon) de cada alcaldía, derivado una vez de neighbourhoods.geojson.
CENTROIDS = {
    "Azcapotzalco": (19.485069, -99.183512),
    "Benito Juárez": (19.380307, -99.164319),
    "Coyoacán": (19.331645, -99.146989),
    "Cuajimalpa de Morelos": (19.322913, -99.318417),
    "Cuauhtémoc": (19.430648, -99.148735),
    "Gustavo A. Madero": (19.512249, -99.104874),
    "Iztacalco": (19.395582, -99.084588),
    "Iztapalapa": (19.339417, -99.048239),
    "La Magdalena Contreras": (19.274538, -99.261870),
    "Miguel Hidalgo": (19.418952, -99.215820),
    "Milpa Alta": (19.190229, -99.042410),
    "Tlalpan": (19.248959, -99.187724),
    "Tláhuac": (19.268511, -99.008906),
    "Venustiano Carranza": (19.434371, -99.093539),
    "Xochimilco": (19.236600, -99.111633),
    "Álvaro Obregón": (19.329316, -99.257731),
}

# Área de la caja envolvente de cada alcaldía: proxy de su tamaño.
BOROUGH_AREAS = {
    "Azcapotzalco": 0.004582,
    "Benito Juárez": 0.002885,
    "Coyoacán": 0.006692,
    "Cuajimalpa de Morelos": 0.020362,
    "Cuauhtémoc": 0.004098,
    "Gustavo A. Madero": 0.018670,
    "Iztacalco": 0.003788,
    "Iztapalapa": 0.020776,
    "La Magdalena Contreras": 0.014562,
    "Miguel Hidalgo": 0.008386,
    "Milpa Alta": 0.037851,
    "Tlalpan": 0.047992,
    "Tláhuac": 0.014997,
    "Venustiano Carranza": 0.004533,
    "Xochimilco": 0.024741,
    "Álvaro Obregón": 0.026123,
}

ROOM_TYPES = ["Entire home/apt", "Hotel room", "Private room", "Shared room"]
BOROUGHS = sorted(CENTROIDS)

# Zócalo: referencia del centro de la ciudad.
CITY_CENTER = (19.4326, -99.1332)

# Medianas del set de entrenamiento, para rellenar campos que lleguen vacíos.
MEDIANS = {
    "bedrooms": 1.0,
    "bathrooms": 1.0,
    "beds": 2.0,
    "minimum_nights": 1.0,
    "maximum_nights": 1125.0,
}

# Tope que usa Airbnb; recortamos ahí para que no distorsione.
MAX_NIGHTS = 1125


def _amenity_column(name: str) -> str:
    """Nombre de columna de una amenidad. Debe coincidir entre train y predict."""
    return "am_" + name.lower().replace(" ", "_")[:28]


def _borough_column(name: str) -> str:
    return "dcen_" + name.lower().replace(" ", "_")[:16]


def _distance(lat, lon, lat0, lon0):
    """Distancia euclidiana en grados. Basta como proxy: el modelo solo necesita
    una medida monótona de cercanía, no kilómetros exactos."""
    return np.sqrt((lat - lat0) ** 2 + (lon - lon0) ** 2)


def build(data: pd.DataFrame) -> pd.DataFrame:
    """Convierte datos crudos de propiedades en la matriz numérica del modelo.

    Espera las columnas: accommodates, bedrooms, bathrooms, beds, latitude,
    longitude, room_type, neighbourhood_cleansed, amenities (lista o texto),
    minimum_nights, maximum_nights, bathrooms_text.

    Devuelve un DataFrame con las columnas en orden fijo (ver `column_order()`).
    """
    src = data.reset_index(drop=True)
    out = pd.DataFrame(index=src.index)

    # --- Capacidad ---
    for col in ["accommodates", "bedrooms", "bathrooms", "beds"]:
        out[col] = pd.to_numeric(src[col], errors="coerce").fillna(MEDIANS.get(col, 1.0))

    out["latitude"] = pd.to_numeric(src["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(src["longitude"], errors="coerce")

    # --- One-hot de categorías: generamos todas las columnas posibles, para que el
    # orden no dependa de qué valores traiga este lote de datos. ---
    for room_type in ROOM_TYPES:
        out[f"room_type_{room_type}"] = (src["room_type"] == room_type).astype(int)
    for borough in BOROUGHS:
        out[f"neighbourhood_cleansed_{borough}"] = (src["neighbourhood_cleansed"] == borough).astype(int)

    # --- Amenidades del catálogo ---
    text = src["amenities"].apply(
        lambda v: " ".join(v).lower() if isinstance(v, list) else str(v).lower()
    )
    for amenity in AMENITY_CATALOG:
        out[_amenity_column(amenity)] = text.str.contains(amenity.lower(), regex=False).astype(int)
    out["n_amenities"] = out[[_amenity_column(a) for a in AMENITY_CATALOG]].sum(axis=1)

    # --- Proporciones: qué tan holgada es la propiedad ---
    guests = out["accommodates"].clip(lower=1)
    out["baths_per_guest"] = out["bathrooms"] / guests
    out["beds_per_guest"] = out["beds"] / guests
    out["guests_per_bedroom"] = out["accommodates"] / out["bedrooms"].clip(lower=1)

    # --- Geografía: todo sale de lat/long más las constantes de arriba ---
    lat, lon = out["latitude"], out["longitude"]
    out["dist_city_center"] = _distance(lat, lon, *CITY_CENTER)

    borough_lat = src["neighbourhood_cleansed"].map(lambda n: CENTROIDS.get(n, (np.nan, np.nan))[0])
    borough_lon = src["neighbourhood_cleansed"].map(lambda n: CENTROIDS.get(n, (np.nan, np.nan))[1])
    out["dist_borough_centroid"] = _distance(lat, lon, borough_lat, borough_lon)
    out["borough_area"] = src["neighbourhood_cleansed"].map(BOROUGH_AREAS)

    # Distancia a cada alcaldía: le da al modelo la posición relativa en la ciudad.
    for name, (blat, blon) in CENTROIDS.items():
        out[_borough_column(name)] = _distance(lat, lon, blat, blon)

    # --- Reglas de estancia (las define el administrador) ---
    out["minimum_nights"] = (pd.to_numeric(src["minimum_nights"], errors="coerce")
                             .fillna(MEDIANS["minimum_nights"]))
    out["maximum_nights"] = (pd.to_numeric(src["maximum_nights"], errors="coerce")
                             .fillna(MEDIANS["maximum_nights"]).clip(upper=MAX_NIGHTS))

    # --- Tipo de baño: el número de baños no dice si es privado o compartido ---
    bath_text = src["bathrooms_text"].fillna("").astype(str).str.lower()
    out["shared_bath"] = bath_text.str.contains("shared").astype(int)
    out["private_bath"] = bath_text.str.contains("private").astype(int)
    out["half_bath"] = bath_text.str.contains("half").astype(int)

    return out


def column_order() -> list[str]:
    """Orden esperado de las features. El modelo predice basura si llegan en otro
    orden, así que al predecir se reindexa contra esta lista."""
    sample = pd.DataFrame([{
        "accommodates": 2, "bedrooms": 1, "bathrooms": 1, "beds": 1,
        "latitude": CITY_CENTER[0], "longitude": CITY_CENTER[1],
        "room_type": ROOM_TYPES[0], "neighbourhood_cleansed": BOROUGHS[0],
        "amenities": [], "minimum_nights": 1, "maximum_nights": 30,
        "bathrooms_text": "1 bath",
    }])
    return list(build(sample).columns)
