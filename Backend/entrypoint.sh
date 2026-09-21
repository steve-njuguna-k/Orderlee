#!/bin/bash
set -e

echo "Applying database migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Creating a super user..."
python manage.py create_superadmin

echo "Starting Django server..."
exec python manage.py runserver 0.0.0.0:9000