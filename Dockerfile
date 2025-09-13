FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Core build tools + libs for Pillow/ReportLab/Postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    libpq-dev \
    zlib1g-dev \
    libjpeg62-turbo-dev \
    libpng-dev \
    libtiff5-dev \
    libfreetype6-dev \
    libwebp-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PostgreSQL client
RUN apt-get update && apt-get install -y postgresql-client

# Install deps first to leverage layer caching
COPY requirements.txt /app/
RUN python -V && pip -V && pip install --no-cache-dir -r requirements.txt

# App code
COPY . /app

EXPOSE 8000
# Replace "eventlinez" if your Django project package differs
CMD ["gunicorn", "eventlinez.wsgi:application", "--bind", "0.0.0.0:8000"]
