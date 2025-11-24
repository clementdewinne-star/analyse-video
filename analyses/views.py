from django.shortcuts import render
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Video, Sequence
from .ai_google import analyse_tactique
import json
import os
import time
from moviepy import VideoFileClip
from docx import Document # N'oublie pas : pip install python-docx

def liste_videos(request):
    videos = Video.objects.all()
    return render(request, 'index.html', {'videos': videos})

# --- OUTIL : GÉNÉRER WORD ---
def generer_word(texte_ia, titre):
    doc = Document()
    doc.add_heading(f'Rapport : {titre}', 0)
    doc.add_paragraph(texte_ia)
    
    nom_fichier = f"Rapport_{int(time.time())}.docx"
    dossier = os.path.join(settings.MEDIA_ROOT, 'rapports')
    os.makedirs(dossier, exist_ok=True)
    path = os.path.join(dossier, nom_fichier)
    
    doc.save(path)
    return f"/media/rapports/{nom_fichier}"

# --- 1. ANALYSE CLIP ENTIER ---
def analyser_video_entiere(request, video_id):
    try:
        video = Video.objects.get(id=video_id)
        rapport = analyse_tactique(video.fichier_video.path)
        url_word = generer_word(rapport, video.titre)
        return JsonResponse({'status': 'ok', 'rapport': rapport, 'url_word': url_word})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# --- 2. ANALYSE SÉQUENCE ---
def analyser_sequence_ia(request, seq_id):
    try:
        seq = Sequence.objects.get(id=seq_id)
        rapport = analyse_tactique(seq.video.fichier_video.path, seq.temps_debut, seq.temps_fin)
        url_word = generer_word(rapport, f"{seq.label} ({seq.video.titre})")
        return JsonResponse({'status': 'ok', 'rapport': rapport, 'url_word': url_word})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# --- 3. TÉLÉCHARGEMENT ---
def telecharger_sequence(request, seq_id):
    try:
        seq = Sequence.objects.get(id=seq_id)
        nom = f"{seq.label}_{seq.temps_debut}.mp4".replace(" ", "_")
        dossier = os.path.join(settings.MEDIA_ROOT, 'clips')
        os.makedirs(dossier, exist_ok=True)
        path_out = os.path.join(dossier, nom)
        if not os.path.exists(path_out):
            with VideoFileClip(seq.video.fichier_video.path) as v:
                v.subclipped(seq.temps_debut, seq.temps_fin).write_videofile(path_out, codec="libx264", audio_codec="aac", preset='ultrafast', logger=None)
        return FileResponse(open(path_out, 'rb'), as_attachment=True)
    except Exception as e: return HttpResponse(str(e))

# --- 4. TAGGING ---
@csrf_exempt 
def ajouter_tag(request):
    if request.method == 'POST':
        try:
            d = json.loads(request.body)
            v = Video.objects.get(id=d.get('video_id'))
            mode = d.get('mode')
            if mode == 'manual':
                t1, t2 = float(d.get('start_time') or 0), float(d.get('end_time') or 0)
            else:
                t = float(d.get('temps') or 0)
                t1, t2 = max(0, t - float(d.get('lag', 5))), t + float(d.get('lead', 5))
            Sequence.objects.create(video=v, label=d.get('label'), temps_debut=round(t1,1), temps_fin=round(t2,1))
            return JsonResponse({'status': 'ok'})
        except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error'})

