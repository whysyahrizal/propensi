#!/usr/bin/env bash
# Exit on error
set -o errexit

# Modify this line as needed for your package manager (pip, poetry, etc.)
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Create migration files if models changed (commit these from local when possible)
python manage.py makemigrations --no-input

# Apply any outstanding database migrations
python manage.py migrate

# Seed initial data (Satker, Roles, Superadmin)
python manage.py seed_data
