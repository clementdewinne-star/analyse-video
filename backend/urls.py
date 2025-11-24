from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from analyses.views import (
    liste_videos, ajouter_tag, telecharger_sequence, 
    analyser_sequence_ia, analyser_video_entiere, lancer_spotlight
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', liste_videos, name='accueil'),
    path('api/tag/', ajouter_tag, name='api_tag'),
    path('download/<int:seq_id>/', telecharger_sequence, name='dl_seq'),
    path('ai/sequence/<int:seq_id>/', analyser_sequence_ia, name='ai_seq'),
    path('ai/video/<int:video_id>/', analyser_video_entiere, name='ai_full_video'),
    path('ai/spotlight/<int:video_id>/', lancer_spotlight, name='ai_spot'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    