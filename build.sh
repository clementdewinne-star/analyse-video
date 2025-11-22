#!/usr/bin/env bash
# Arrêter le script si une erreur survient
set -o errexit

# 1. Installer les ingrédients
pip install -r requirements.txt

# 2. RASSEMBLER LE DESIGN (La ligne magique ✨)
python manage.py collectstatic --no-input

# 3. Construire la base de données
python manage.py migrate

# 4. Créer le Superuser (Admin)
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')"
