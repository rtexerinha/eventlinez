#!/bin/bash

# Check if PostgreSQL is running
echo "Checking PostgreSQL connection..."

if python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        dbname='${POSTGRES_DB:-eventlinez}',
        user='${POSTGRES_USER:-eventlinez}',
        password='${POSTGRES_PASSWORD:-Texera123@}',
        host='${POSTGRES_HOST:-localhost}',
        port='${POSTGRES_PORT:-5432}'
    )
    conn.close()
    print('PostgreSQL connection successful')
    exit(0)
except Exception as e:
    print(f'PostgreSQL connection failed: {e}')
    exit(1)
"; then
    echo "Starting server with PostgreSQL database..."

    # Run migrations with PostgreSQL
    python manage.py migrate

    # Start server with PostgreSQL
    python manage.py runserver 0.0.0.0:8000
else
    echo "PostgreSQL is not available. Starting server with SQLite database..."

    # Set environment variable for SQLite
    export USE_SQLITE=true

    # Run migrations with SQLite
    python manage.py migrate --use-sqlite

    # Start server with SQLite
    python manage.py runserver --use-sqlite 0.0.0.0:8000
fi
