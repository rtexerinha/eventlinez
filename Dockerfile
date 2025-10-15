FROM python:3.9.24-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    IN_DOCKER=true

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
    postgresql-client \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create virtual environment in /opt/venv to avoid conflicts with local .venv
RUN python -m venv $VIRTUAL_ENV

# Upgrade pip and install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Create necessary directories
RUN mkdir -p /app/media /app/staticfiles

# Create entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set proper permissions
RUN chmod -R 755 /app

EXPOSE 8000

# Use entrypoint script to handle migrations and static files
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "eventlinez.wsgi:application", "--bind", "0.0.0.0:8000"]
