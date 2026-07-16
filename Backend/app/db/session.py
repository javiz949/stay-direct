from sqlmodel import Session, create_engine

from app.core.config import settings

# El engine es un pool de conexiones, no una conexión: no toca Postgres hasta
# la primera query. Va a nivel de módulo para crearse una sola vez y que lo
# comparta toda la app (dentro de una función crearía un pool por request).
# echo=True imprime el SQL generado en la terminal; apagar en producción.
engine = create_engine(settings.database_url, echo=True)


def get_session():
    # yield y no return: pausa aquí y le entrega la sesión a FastAPI durante el
    # request; al terminar se reanuda, sale del with y la cierra sola — incluso
    # si el endpoint lanzó una excepción. Así no se fugan conexiones.
    with Session(engine) as session:
        yield session
