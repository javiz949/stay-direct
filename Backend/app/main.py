from fastapi import FastAPI

# El objeto central de la app: aquí se cuelgan los routers de cada feature
# (properties, bookings, ...). El title es lo que se ve en la doc /docs.
app = FastAPI(title="Stay Direct API")


@app.get("/health")
def health():
    # Endpoint de salud: confirma que el servidor está vivo sin tocar la DB.
    # En el Módulo 3, Docker lo usará para saber si este servicio ya arrancó.
    return {"status": "ok"}
