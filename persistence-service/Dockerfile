FROM python:3.10-slim

WORKDIR /app

COPY persistence-service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/models ./backend/models
COPY backend/cores ./backend/cores
COPY backend/databases ./backend/databases
COPY backend/schemas ./backend/schemas

COPY persistence-service/persistence_service.py .

ENV PYTHONPATH=/app

CMD ["python", "persistence_service.py"]
