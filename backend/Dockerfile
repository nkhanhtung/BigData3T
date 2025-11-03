
FROM python:3.10-slim AS builder

WORKDIR /app

RUN pip install --upgrade pip

COPY ./requirements.txt .

RUN pip install --prefix=/install -r requirements.txt

FROM python:3.10-slim

WORKDIR /app

COPY --from=builder /install /usr/local

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
