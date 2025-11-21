from django.contrib import admin
from .models import Video, Sequence

# Cette astuce permet de voir les séquences DIRECTEMENT dans la fiche de la vidéo
class SequenceInline(admin.TabularInline):
    model = Sequence
    extra = 1

class VideoAdmin(admin.ModelAdmin):
    inlines = [SequenceInline]

admin.site.register(Video, VideoAdmin)
admin.site.register(Sequence)
