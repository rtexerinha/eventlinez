#!/bin/sh

echo "Starting Gunicorn..."
exec gunicorn -b 0.0.0.0:8000 eventlinez.wsgi:application
