#!/usr/bin/env bash
# Arrêter le script si une erreur survient
set -o errexit

# 1. Installer les ingrédients
pip install -r requirements.txt

# 2. Construire la base de données (Migrate)
python manage.py migrate

# 3. Créer le Superuser automatiquement (admin / admin123)
# Ce script vérifie si 'admin' existe déjà. Si non, il le crée.
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')"
