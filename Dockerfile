# image: python:3.10
FROM python:3.10

# Installing system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y postgresql-client

WORKDIR /app

COPY . .

# Installing Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install gunicorn

# Create a script to run the application
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
