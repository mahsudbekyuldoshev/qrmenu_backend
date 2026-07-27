FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync

COPY . .

# Ma'lumotlar bazasi migratsiyalarini avtomatik yurgizish va serverni Gunicorn orqali ochish
CMD ["uv", "run", "gunicorn", "root.wsgi:application", "--bind", "0.0.0.0:8000"]