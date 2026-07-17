from sqlmodel import Session, select

from app.models.property import Property


# Única capa que toca Postgres. Recibe la sesión (no la crea): así el llamador
# controla la transacción y el repo se puede probar con una sesión de prueba.
def create(session: Session, property: Property) -> Property:
    session.add(property)
    session.commit()
    # refresh recarga el objeto con lo que puso la DB (id, created_at).
    session.refresh(property)
    return property


def get_all(session: Session) -> list[Property]:
    return list(session.exec(select(Property)).all())


# None cuando el id no existe; el service lo traducirá a 404.
def get_by_id(session: Session, property_id: int) -> Property | None:
    return session.get(Property, property_id)


# Misma operación que create a nivel DB: la sesión rastrea el objeto y el commit
# hace INSERT o UPDATE según corresponda. También la usa el borrado suave.
def update(session: Session, property: Property) -> Property:
    session.add(property)
    session.commit()
    session.refresh(property)
    return property
