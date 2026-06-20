# Imagen del backend (FastAPI). El contexto de build es la raíz del repo.
FROM python:3.12-slim

WORKDIR /app

# Dependencias primero, para aprovechar la caché de capas de Docker.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

# ChromaDB persiste aquí (montado como volumen en docker-compose).
ENV CHROMA_PATH=/data/chroma_db

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
