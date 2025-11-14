FROM python:3.10-slim

WORKDIR /app

COPY persistence-service/requirements.txt .

COPY backend ./backend

RUN pip install -r requirements.txt

COPY persistence-service/persistence_service.py .

ENV PYTHONPATH=/app/backend

CMD ["python", "persistence_service.py"]
