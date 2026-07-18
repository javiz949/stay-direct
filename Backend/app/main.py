from fastapi import FastAPI
from contextlib import asynccontextmanager

from sqlmodel import SQLModel

from app.db.session import engine
from app.models.booking import Booking  # noqa: F401
from app.models.property import Property  # noqa: F401
from app.models.user import User  # noqa: F401
from app.api import auth, bookings, properties

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

# El objeto central de la app: aquí se cuelgan los routers de cada feature
# (properties, bookings, ...). El title es lo que se ve en la doc /docs.

app = FastAPI(title="Stay Direct API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(bookings.router)


@app.get("/health")
def health():
    # Endpoint de salud: confirma que el servidor está vivo sin tocar la DB.
    # En el Módulo 3, Docker lo usará para saber si este servicio ya arrancó.
    return {"status": "ok"}
