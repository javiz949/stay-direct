FROM python:3.13-slim

WORKDIR /service

# Las dependencias primero y en su propia capa: si solo cambia el código, Docker
# reutiliza esta capa y no reinstala todo.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
