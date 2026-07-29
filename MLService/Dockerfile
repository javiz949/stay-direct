FROM python:3.13-slim

WORKDIR /service

# Las dependencias primero y en su propia capa: si solo cambia el código, Docker
# reutiliza esta capa y no reinstala pandas/sklearn (que tardan).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# El artefacto va dentro de la imagen para que el contenedor arranque sin
# necesitar entrenar ni montar volúmenes.
COPY app/ ./app/
COPY artifacts/ ./artifacts/

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
