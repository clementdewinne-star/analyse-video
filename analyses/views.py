from django.shortcuts import render
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Video, Sequence
from .ai_google import analyse_tactique
from .ai_tracking import generer_tracking_spotlight
import json
import os
import time
import requests 
from moviepy import VideoFileClip
from docx import Document

def liste_videos(request):
    videos = Video.objects.all()
    return render(request, 'index.html', {'videos': videos})

def generer_word(texte, titre):
    doc = Document()
    doc.add_heading(f'Rapport : {titre}', 0)
    doc.add_paragraph(texte)
    nom = f"Rapport_{int(time.time())}.docx"
    d = os.path.join(settings.MEDIA_ROOT, 'rapports')
    os.makedirs(d, exist_ok=True)
    doc.save(os.path.join(d, nom))
    return f"/media/rapports/{nom}"

# --- IA TACTIQUE (WORD) ---
def analyser_video_entiere(request, video_id):
    try:
        v = Video.objects.get(id=video_id)
        rap = analyse_tactique(v.fichier_video.url)
        url = generer_word(rap, v.titre)
        return JsonResponse({'status': 'ok', 'rapport': rap, 'url_word': url})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

def analyser_sequence_ia(request, seq_id):
    try:
        s = Sequence.objects.get(id=seq_id)
        rap = analyse_tactique(s.video.fichier_video.url, s.temps_debut, s.temps_fin)
        url = generer_word(rap, s.label)
        return JsonResponse({'status': 'ok', 'rapport': rap, 'url_word': url})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

# --- FONCTION SPOTLIGHT (Visualisation Directe) ---
def lancer_spotlight(request, video_id):
    try:
        video = Video.objects.get(id=video_id)
        
        # On lance le traitement qui va uploader sur Cloudinary
        url_resultat = generer_tracking_spotlight(video.fichier_video.url, video_id)
        
        if not url_resultat:
            return JsonResponse({'status': 'error', 'message': "Échec du traitement vidéo"})
            
        # On renvoie l'URL pour lecture immédiate
        return JsonResponse({'status': 'ok', 'video_url': url_resultat})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# --- DOWNLOAD ---
def telecharger_sequence(request, seq_id):
    try:
        s = Sequence.objects.get(id=seq_id)
        path_dl = f"temp_{int(time.time())}.mp4"
        with requests.get(s.video.fichier_video.url, stream=True) as r:
            with open(path_dl, 'wb') as f:
                for c in r.iter_content(8192): f.write(c)
        
        nom_out = f"{s.label}.mp4"
        path_out = "out_" + path_dl
        with VideoFileClip(path_dl) as v:
            v.subclipped(s.temps_debut, s.temps_fin).write_videofile(path_out, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
        
        f = open(path_out, 'rb')
        # os.remove(path_dl) # Nettoyage optionnel
        return FileResponse(f, as_attachment=True, filename=nom_out)
    except Exception as e: return HttpResponse(str(e))

# --- TAGGING ---
@csrf_exempt 
def ajouter_tag(request):
    if request.method == 'POST':
        try:
            d = json.loads(request.body)
            v = Video.objects.get(id=d.get('video_id'))
            mode = d.get('mode')
            if mode == 'manual': t1, t2 = float(d.get('start_time') or 0), float(d.get('end_time') or 0)
            else: t=float(d.get('temps') or 0); t1, t2 = max(0, t-float(d.get('lag', 5))), t+float(d.get('lead', 5))
            Sequence.objects.create(video=v, label=d.get('label'), temps_debut=round(t1,1), temps_fin=round(t2,1))
            return JsonResponse({'status': 'ok'})
        except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error'})
