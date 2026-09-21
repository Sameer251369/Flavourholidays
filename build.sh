#!/usr/bin/env bash
# exit on error
set -o errexit

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --no-input

echo "==> Running database migrations..."
python manage.py migrate

echo "==> Seeding initial data (if database is empty)..."
python manage.py seed_data

echo "==> Render build finished successfully!"
