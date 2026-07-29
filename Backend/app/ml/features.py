"""Construcción de features del modelo de precio.

Este módulo es la ÚNICA fuente de verdad de las features: lo importan tanto el
entrenamiento (`train.py`) como el microservicio de predicción. Si la lógica
viviera duplicada en los dos lados, se desincronizarían y el modelo recibiría
features distintas al entrenar y al predecir (training-serving skew).

Las constantes geográficas y el catálogo de amenidades están congelados aquí a
propósito: el microservicio no necesita el CSV ni el geojson en tiempo de
ejecución, solo aritmética.
"""

import numpy as np
import pandas as pd

# Catálogo de amenidades del modelo: las 40 más frecuentes del mercado de CDMX.
# Es tambien el catálogo que debe ofrecer el formulario del backend, para que
# entrenamiento y producción coincidan. Se probaron 14/25/40/60/80: 40 fue el
# óptimo; más allá, las amenidades poco frecuentes meten ruido.
CATALOGO_AMENIDADES = [
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
CENTROIDES = {
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
AREAS = {
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
ALCALDIAS = sorted(CENTROIDES)

# Zócalo: referencia del centro de la ciudad.
CENTRO_CDMX = (19.4326, -99.1332)

# Medianas del set de entrenamiento, para rellenar campos que lleguen vacíos.
MEDIANAS = {
    "bedrooms": 1.0,
    "bathrooms": 1.0,
    "beds": 2.0,
    "minimum_nights": 1.0,
    "maximum_nights": 1125.0,
}

# Tope que usa Airbnb; recortamos ahí para que no distorsione.
MAX_NOCHES = 1125


def _slug_amenidad(nombre: str) -> str:
    """Nombre de columna a partir de una amenidad. Debe coincidir en train y predict."""
    return "am_" + nombre.lower().replace(" ", "_")[:28]


def _slug_alcaldia(nombre: str) -> str:
    return "dcen_" + nombre.lower().replace(" ", "_")[:16]


def _distancia(lat, lon, lat0, lon0):
    """Distancia euclidiana en grados. Basta como proxy: el modelo solo necesita
    una medida monótona de cercanía, no kilómetros exactos."""
    return np.sqrt((lat - lat0) ** 2 + (lon - lon0) ** 2)


def construir(datos: pd.DataFrame) -> pd.DataFrame:
    """Convierte datos crudos de propiedades en la matriz numérica del modelo.

    Espera las columnas: accommodates, bedrooms, bathrooms, beds, latitude,
    longitude, room_type, neighbourhood_cleansed, amenities (lista o texto),
    minimum_nights, maximum_nights, bathrooms_text.

    Devuelve un DataFrame con las columnas en orden fijo (ver `columnas()`).
    """
    d = datos.reset_index(drop=True)
    out = pd.DataFrame(index=d.index)

    # --- Capacidad ---
    for c in ["accommodates", "bedrooms", "bathrooms", "beds"]:
        out[c] = pd.to_numeric(d[c], errors="coerce").fillna(MEDIANAS.get(c, 1.0))

    out["latitude"] = pd.to_numeric(d["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(d["longitude"], errors="coerce")

    # --- One-hot de categorías: se generan todas las columnas posibles, para que
    # el orden no dependa de qué valores traiga este lote de datos. ---
    for rt in ROOM_TYPES:
        out[f"room_type_{rt}"] = (d["room_type"] == rt).astype(int)
    for al in ALCALDIAS:
        out[f"neighbourhood_cleansed_{al}"] = (d["neighbourhood_cleansed"] == al).astype(int)

    # --- Amenidades del catálogo ---
    texto = d["amenities"].apply(
        lambda v: " ".join(v).lower() if isinstance(v, list) else str(v).lower()
    )
    for a in CATALOGO_AMENIDADES:
        out[_slug_amenidad(a)] = texto.str.contains(a.lower(), regex=False).astype(int)
    out["n_amenidades"] = out[[_slug_amenidad(a) for a in CATALOGO_AMENIDADES]].sum(axis=1)

    # --- Proporciones: qué tan holgada es la propiedad ---
    huesp = out["accommodates"].clip(lower=1)
    out["banos_x_huesp"] = out["bathrooms"] / huesp
    out["camas_x_huesp"] = out["beds"] / huesp
    out["huesp_x_rec"] = out["accommodates"] / out["bedrooms"].clip(lower=1)

    # --- Geografía: todo sale de lat/long más las constantes de arriba ---
    lat, lon = out["latitude"], out["longitude"]
    out["dist_centro"] = _distancia(lat, lon, *CENTRO_CDMX)

    clat = d["neighbourhood_cleansed"].map(lambda n: CENTROIDES.get(n, (np.nan, np.nan))[0])
    clon = d["neighbourhood_cleansed"].map(lambda n: CENTROIDES.get(n, (np.nan, np.nan))[1])
    out["dist_centroide_alcaldia"] = _distancia(lat, lon, clat, clon)
    out["area_alcaldia"] = d["neighbourhood_cleansed"].map(AREAS)

    # Distancia a cada alcaldía: le da al modelo la posición relativa en la ciudad.
    for nombre, (la, ln) in CENTROIDES.items():
        out[_slug_alcaldia(nombre)] = _distancia(lat, lon, la, ln)

    # --- Reglas de estancia (las define el administrador) ---
    out["minimum_nights"] = pd.to_numeric(d["minimum_nights"], errors="coerce").fillna(MEDIANAS["minimum_nights"])
    out["maximum_nights"] = (pd.to_numeric(d["maximum_nights"], errors="coerce")
                             .fillna(MEDIANAS["maximum_nights"]).clip(upper=MAX_NOCHES))

    # --- Tipo de baño: el número de baños no dice si es privado o compartido ---
    bt = d["bathrooms_text"].fillna("").astype(str).str.lower()
    out["bano_compartido"] = bt.str.contains("shared").astype(int)
    out["bano_privado"] = bt.str.contains("private").astype(int)
    out["medio_bano"] = bt.str.contains("half").astype(int)

    return out


def columnas() -> list[str]:
    """Orden esperado de las features. El modelo predice basura si llegan en otro
    orden, así que el microservicio reindexa contra esta lista."""
    fila = pd.DataFrame([{
        "accommodates": 2, "bedrooms": 1, "bathrooms": 1, "beds": 1,
        "latitude": CENTRO_CDMX[0], "longitude": CENTRO_CDMX[1],
        "room_type": ROOM_TYPES[0], "neighbourhood_cleansed": ALCALDIAS[0],
        "amenities": [], "minimum_nights": 1, "maximum_nights": 30,
        "bathrooms_text": "1 bath",
    }])
    return list(construir(fila).columns)
