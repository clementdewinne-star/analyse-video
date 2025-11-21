from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# On importe les fonctions depuis le dossier 'analyses'
from analyses.views import liste_videos, ajouter_tag, telecharger_sequence

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', liste_videos, name='accueil'),
    path('api/tag/', ajouter_tag, name='api_tag'),
    path('download/<int:seq_id>/', telecharger_sequence, name='dl_seq'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    