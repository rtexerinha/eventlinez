#!/bin/sh

# Function to wait for the database to be ready
function postgres_ready(){
python << END
import sys
import psycopg2
import os

try:
    dbname = os.getenv("POSTGRES_DB", "eventlinez")
    user = os.getenv("POSTGRES_USER", "eventlinez")
    password = os.getenv("POSTGRES_PASSWORD", "Texera123@")
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")

    print(f"Attempting to connect to PostgreSQL at {host}:{port}")
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
    conn.close()
    print("PostgreSQL connection successful")
except psycopg2.OperationalError as e:
    print(f"PostgreSQL connection failed: {e}")
    sys.exit(-1)
sys.exit(0)
END
}

# Wait for the database to be ready
until postgres_ready; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "PostgreSQL is up - continuing..."

echo "Starting Gunicorn..."
exec gunicorn -b 0.0.0.0:8000 eventlinez.wsgi:application
