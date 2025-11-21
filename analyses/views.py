from django.shortcuts import render
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Video, Sequence
import json
import os

# Import de l'outil de montage vidéo
from moviepy import VideoFileClip

def liste_videos(request):
    videos = Video.objects.all()
    return render(request, 'index.html', {'videos': videos})

# --- FONCTION DE TÉLÉCHARGEMENT ---
def telecharger_sequence(request, seq_id):
    try:
        # 1. On récupère la séquence
        seq = Sequence.objects.get(id=seq_id)
        video_path = seq.video.fichier_video.path
        
        # 2. On définit le nom du futur fichier
        # On remplace les espaces par des tirets pour éviter les bugs
        nom_fichier = f"{seq.label}_{seq.temps_debut}_{seq.temps_fin}.mp4".replace(" ", "_")
        dossier_temp = os.path.join(settings.MEDIA_ROOT, 'clips')
        
        if not os.path.exists(dossier_temp):
            os.makedirs(dossier_temp)
            
        chemin_sortie = os.path.join(dossier_temp, nom_fichier)

        # 3. SI LE FICHIER N'EXISTE PAS, ON LE CRÉE
        if not os.path.exists(chemin_sortie):
            print(f"Découpage en cours : {seq.label}...")
            
            # Découpage avec MoviePy
            with VideoFileClip(video_path) as video:
                clip = video.subclipped(seq.temps_debut, seq.temps_fin)
                # preset='ultrafast' pour que ça aille vite
                clip.write_videofile(chemin_sortie, codec="libx264", audio_codec="aac", preset='ultrafast', logger=None)

        # 4. On envoie le fichier
        return FileResponse(open(chemin_sortie, 'rb'), as_attachment=True)

    except Exception as e:
        return HttpResponse(f"Erreur lors du découpage : {str(e)}")


# --- FONCTION DE TAGGING ---
@csrf_exempt 
def ajouter_tag(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            video_id = data.get('video_id')
            label = data.get('label')
            mode = data.get('mode') 
            
            video = Video.objects.get(id=video_id)
            
            if mode == 'manual':
                t_debut = float(data.get('start_time') or 0)
                t_fin = float(data.get('end_time') or 0)
            else:
                temps_clic = float(data.get('temps') or 0)
                lag = float(data.get('lag', 5))
                lead = float(data.get('lead', 5))
                t_debut = max(0, temps_clic - lag)
                t_fin = temps_clic + lead

            Sequence.objects.create(
                video=video,
                label=label,
                temps_debut=round(t_debut, 1),
                temps_fin=round(t_fin, 1)
            )
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            print("ERREUR:", e)
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error'})
