"""
Seed de datos simulados pero realistas (Ciudad de México) para el catálogo.
Idempotente: si una amenidad o propiedad ya existe (por nombre/título), no la duplica.
Correr desde Backend/ con el venv activo:  python seed_data.py
"""
from decimal import Decimal

from sqlmodel import Session, select

from app.db.session import engine
from app.models.amenity import Amenity
from app.models.property import Property

# Catálogo curado (~14): amenidades que DIFERENCIAN, no las 40 de Airbnb.
AMENIDADES = [
    "Wifi",
    "Cocina",
    "Aire acondicionado",
    "Agua caliente",
    "Refrigerador",
    "Lavadora",
    "Estacionamiento gratis",
    "Cochera privada",
    "Alberca",
    "TV con streaming",
    "Área de trabajo",
    "Gimnasio",
    "Detector de humo",
    "Pet friendly",
]

# (title, description, city, neighborhood, address, property_type,
#  max_guests, bedrooms, bathrooms, price_per_night, [amenidades])
#
# OJO con `neighborhood`: guarda la ALCALDÍA, no la colonia. Es el campo que
# consume el modelo de precios, y solo conoce las 16 alcaldías de CDMX con las
# que se entrenó (ver CENTROIDS en MLService/app/features.py). La colonia va en
# el título y la dirección, que además es como se escribe una dirección real.
#
# Agrupadas en 4 clusters de precio para que el catálogo tenga estructura clara.
PROPIEDADES = [
    # --- Cluster A: ECONÓMICO (estudios/lofts, alcaldías periféricas) ~550-1150 ---
    ("Estudio funcional en Azcapotzalco", "Estudio sencillo y bien conectado, a unas cuadras del metro.", "Ciudad de México", "Azcapotzalco", "Av. Cuitláhuac 1520, Col. Petrolera", "estudio", 2, 0, 1, "650.00", ["Wifi", "Cocina", "Agua caliente", "Refrigerador"]),
    ("Loft sencillo cerca de La Villa", "Loft práctico a caminando de la Basílica de Guadalupe.", "Ciudad de México", "Gustavo A. Madero", "Calzada de Guadalupe 480, Col. Estrella", "loft", 2, 1, 1, "700.00", ["Wifi", "Cocina", "Agua caliente"]),
    ("Departamento económico en Iztacalco", "Departamento funcional en zona tranquila, cerca del Palacio de los Deportes.", "Ciudad de México", "Iztacalco", "Av. Río Churubusco 920, Col. Agrícola Oriental", "departamento", 3, 1, 1, "620.00", ["Wifi", "Cocina", "Agua caliente", "Refrigerador"]),
    ("Estudio compacto cerca del Aeropuerto", "Ideal para escalas o viajes cortos: a 10 minutos de la Terminal 1.", "Ciudad de México", "Venustiano Carranza", "Blvd. Puerto Aéreo 340, Col. Moctezuma", "estudio", 2, 0, 1, "750.00", ["Wifi", "Cocina", "Agua caliente", "Refrigerador", "Área de trabajo"]),
    ("Departamento sencillo en Iztapalapa", "Opción económica en una zona residencial bien comunicada.", "Ciudad de México", "Iztapalapa", "Av. Tláhuac 1180, Col. Santa María Aztahuacán", "departamento", 3, 1, 1, "550.00", ["Wifi", "Cocina", "Agua caliente"]),
    ("Departamento acogedor en Portales", "Departamento cómodo en una colonia tradicional, cerca del metro Portales.", "Ciudad de México", "Benito Juárez", "Calle Cuauhtémoc 720, Col. Portales Norte", "departamento", 3, 1, 1, "1100.00", ["Wifi", "Cocina", "Agua caliente", "Refrigerador", "TV con streaming"]),
    ("Loft pequeño en la Doctores", "Loft céntrico a minutos del Centro Histórico y la Roma.", "Ciudad de México", "Cuauhtémoc", "Dr. Vértiz 210, Col. Doctores", "loft", 2, 1, 1, "950.00", ["Wifi", "Cocina", "Agua caliente", "Refrigerador"]),

    # --- Cluster B: MEDIO (departamentos, zonas céntricas) ~1400-2300 ---
    ("Loft moderno en la Roma Norte", "Loft de diseño en el corazón de la Roma, rodeado de cafés y galerías.", "Ciudad de México", "Cuauhtémoc", "Calle Orizaba 120, Col. Roma Norte", "loft", 2, 1, 1, "1850.00", ["Wifi", "Cocina", "Aire acondicionado", "Agua caliente", "Refrigerador", "TV con streaming", "Área de trabajo"]),
    ("Departamento en la Condesa", "Departamento luminoso a pasos del Parque México.", "Ciudad de México", "Cuauhtémoc", "Av. Ámsterdam 240, Col. Hipódromo", "departamento", 4, 2, 1.5, "2200.00", ["Wifi", "Cocina", "Aire acondicionado", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming", "Área de trabajo"]),
    ("Depa luminoso en Del Valle", "Departamento amplio en una zona residencial céntrica y arbolada.", "Ciudad de México", "Benito Juárez", "Av. Coyoacán 1450, Col. Del Valle Centro", "departamento", 4, 2, 1.5, "1700.00", ["Wifi", "Cocina", "Aire acondicionado", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming"]),
    ("Departamento en Narvarte", "Cómodo y bien ubicado, cerca de restaurantes y del metro Etiopía.", "Ciudad de México", "Benito Juárez", "Calle Torres Adalid 830, Col. Narvarte Poniente", "departamento", 3, 1, 1, "1450.00", ["Wifi", "Cocina", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming"]),
    ("Depa céntrico en la Juárez", "A unos pasos del Ángel de la Independencia y Paseo de la Reforma.", "Ciudad de México", "Cuauhtémoc", "Calle Havre 65, Col. Juárez", "departamento", 3, 1, 1, "1900.00", ["Wifi", "Cocina", "Aire acondicionado", "Agua caliente", "Refrigerador", "TV con streaming", "Área de trabajo"]),
    ("Departamento en el centro de Coyoacán", "En pleno barrio de Coyoacán, cerca del Jardín Centenario.", "Ciudad de México", "Coyoacán", "Calle Francisco Sosa 310, Col. Villa Coyoacán", "departamento", 4, 2, 2, "2100.00", ["Wifi", "Cocina", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming", "Estacionamiento gratis"]),
    ("Depa ejecutivo en Escandón", "Pensado para viajes de trabajo: escritorio, buena conexión y ubicación céntrica.", "Ciudad de México", "Miguel Hidalgo", "Calle Prosperidad 145, Col. Escandón", "departamento", 2, 1, 1, "1950.00", ["Wifi", "Cocina", "Aire acondicionado", "Agua caliente", "Refrigerador", "TV con streaming", "Área de trabajo", "Gimnasio"]),

    # --- Cluster C: PREMIUM (departamentos de lujo) ~3400-6200 ---
    ("Departamento de lujo en Polanco", "Acabados premium en la zona más exclusiva de la ciudad, junto a Masaryk.", "Ciudad de México", "Miguel Hidalgo", "Av. Presidente Masaryk 380, Col. Polanco V Sección", "departamento", 4, 2, 2, "5200.00", ["Wifi", "Cocina", "Aire acondicionado", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming", "Área de trabajo", "Alberca", "Gimnasio", "Cochera privada", "Detector de humo"]),
    ("Penthouse con vista a Reforma", "Penthouse con vista panorámica al Bosque de Chapultepec y Paseo de la Reforma.", "Ciudad de México", "Cuauhtémoc", "Paseo de la Reforma 512, Col. Juárez", "departamento", 6, 3, 3, "6200.00", ["Wifi", "Cocina", "Aire acondicionado", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming", "Área de trabajo", "Alberca", "Gimnasio", "Cochera privada", "Detector de humo"]),
    ("Depa premium en Santa Fe", "Departamento moderno en zona corporativa, junto a Centro Santa Fe.", "Ciudad de México", "Álvaro Obregón", "Av. Santa Fe 495, Col. Santa Fe", "departamento", 5, 2, 2, "3800.00", ["Wifi", "Cocina", "Aire acondicionado", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming", "Área de trabajo", "Gimnasio", "Cochera privada", "Detector de humo"]),
    ("Departamento de diseño en Anzures", "Departamento renovado a minutos de Polanco y del Bosque de Chapultepec.", "Ciudad de México", "Miguel Hidalgo", "Calle Leibnitz 220, Col. Anzures", "departamento", 4, 2, 2, "3400.00", ["Wifi", "Cocina", "Aire acondicionado", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming", "Área de trabajo", "Cochera privada"]),
    ("Loft de lujo en la Condesa", "Loft de autor con acabados finos, ideal para parejas exigentes.", "Ciudad de México", "Cuauhtémoc", "Av. Tamaulipas 155, Col. Condesa", "loft", 2, 1, 1.5, "3600.00", ["Wifi", "Cocina", "Aire acondicionado", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming", "Área de trabajo", "Gimnasio"]),
    ("Depa ejecutivo en Lomas de Chapultepec", "Elegante departamento en una de las zonas residenciales más exclusivas.", "Ciudad de México", "Miguel Hidalgo", "Av. Paseo de las Palmas 1250, Col. Lomas de Chapultepec", "departamento", 4, 2, 2.5, "4800.00", ["Wifi", "Cocina", "Aire acondicionado", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming", "Área de trabajo", "Alberca", "Gimnasio", "Cochera privada", "Detector de humo"]),

    # --- Cluster D: CASAS FAMILIARES (grandes, sur y poniente) ~2200-4200 ---
    ("Casa con jardín en Coyoacán", "Casa con encanto y jardín, en una calle empedrada del Coyoacán tradicional.", "Ciudad de México", "Coyoacán", "Calle Higuera 85, Col. Villa Coyoacán", "casa", 6, 3, 2, "3200.00", ["Wifi", "Cocina", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming", "Cochera privada", "Pet friendly", "Detector de humo"]),
    ("Casa familiar en Tlalpan", "Casa amplia en el sur de la ciudad, cerca del centro histórico de Tlalpan.", "Ciudad de México", "Tlalpan", "Calzada de Tlalpan 4820, Col. Tlalpan Centro", "casa", 7, 3, 2.5, "2600.00", ["Wifi", "Cocina", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming", "Estacionamiento gratis", "Pet friendly"]),
    ("Casa amplia en San Ángel", "Residencia con patio en el barrio colonial de San Ángel, junto al Bazar del Sábado.", "Ciudad de México", "Álvaro Obregón", "Calle Amargura 42, Col. San Ángel", "casa", 8, 4, 3, "4200.00", ["Wifi", "Cocina", "Aire acondicionado", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming", "Cochera privada", "Pet friendly", "Detector de humo"]),
    ("Casa tradicional en Xochimilco", "Casa espaciosa cerca de los embarcaderos, ideal para grupos.", "Ciudad de México", "Xochimilco", "Av. Nuevo León 210, Barrio San Juan", "casa", 8, 4, 2.5, "2200.00", ["Wifi", "Cocina", "Agua caliente", "Refrigerador", "Lavadora", "Estacionamiento gratis", "Pet friendly"]),
    ("Casa entre bosque en Cuajimalpa", "Casa tranquila rodeada de árboles, a minutos del Desierto de los Leones.", "Ciudad de México", "Cuajimalpa de Morelos", "Carretera México-Toluca 1850, Col. El Contadero", "casa", 6, 3, 2, "2900.00", ["Wifi", "Cocina", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming", "Cochera privada", "Pet friendly", "Detector de humo"]),
    ("Casa grande para grupos en Contreras", "Casa amplia con jardín en el sur poniente, perfecta para reuniones familiares.", "Ciudad de México", "La Magdalena Contreras", "Av. San Jerónimo 2450, Col. La Concepción", "casa", 9, 4, 3, "2800.00", ["Wifi", "Cocina", "Agua caliente", "Refrigerador", "Lavadora", "TV con streaming", "Alberca", "Estacionamiento gratis", "Pet friendly"]),
]


def get_or_create_amenities(session: Session) -> dict[str, Amenity]:
    # Idempotente: si la amenidad ya existe la reusa; si no, la crea.
    catalogo: dict[str, Amenity] = {}
    for nombre in AMENIDADES:
        amenity = session.exec(select(Amenity).where(Amenity.name == nombre)).first()
        if amenity is None:
            amenity = Amenity(name=nombre)
            session.add(amenity)
            session.commit()
            session.refresh(amenity)
        catalogo[nombre] = amenity
    return catalogo


def seed_data() -> None:
    with Session(engine) as session:
        catalogo = get_or_create_amenities(session)

        creadas = 0
        for (title, desc, city, neigh, addr, ptype,
             guests, beds, baths, price, amenities) in PROPIEDADES:
            # Idempotente: si ya existe una propiedad con ese título, no la duplica.
            if session.exec(select(Property).where(Property.title == title)).first():
                continue
            prop = Property(
                title=title,
                description=desc,
                city=city,
                neighborhood=neigh,
                address=addr,
                property_type=ptype,
                max_guests=guests,
                bedrooms=beds,
                bathrooms=baths,
                price_per_night=Decimal(price),
            )
            # Conecta las amenidades (M2M): SQLAlchemy llena la tabla puente al hacer commit.
            prop.amenities = [catalogo[a] for a in amenities]
            session.add(prop)
            creadas += 1

        session.commit()
        total_am = len(session.exec(select(Amenity)).all())
        total_prop = len(session.exec(select(Property)).all())
        print(f"Seed listo. Amenidades: {total_am} | Propiedades: {total_prop} (nuevas esta corrida: {creadas})")


if __name__ == "__main__":
    seed_data()
