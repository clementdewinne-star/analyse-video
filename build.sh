#!/usr/bin/env bash
# Arrêter le script si une erreur survient
set -o errexit

# 1. Installer les ingrédients (Django, AI...)
pip install -r requirements.txt

# 2. Rassembler le design (WhiteNoise)
python manage.py collectstatic --no-input

# 3. Construire la base de données
python manage.py migrate

# 4. Créer le compte Admin automatiquement
# Si l'utilisateur 'admin' n'existe pas, il le crée avec le mot de passe 'admin123'
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')"
