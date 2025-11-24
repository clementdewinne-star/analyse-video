import cv2
from ultralytics import YOLO
import os
from django.conf import settings

# Chargement du modèle IA (téléchargement auto au 1er lancement)
model = YOLO('yolov8n.pt') 

def demarrer_tracking(video_path, video_id):
    """
    Lit la vidéo, détecte les personnes et génère un fichier MP4 analysé.
    """
    # 1. Préparation des chemins
    nom_sortie = f"IA_Tracked_{video_id}.mp4"
    dossier_clips = os.path.join(settings.MEDIA_ROOT, 'clips')
    chemin_sortie = os.path.join(dossier_clips, nom_sortie)
    
    # Création du dossier si inexistant
    os.makedirs(dossier_clips, exist_ok=True)

    # 2. Lecture vidéo
    cap = cv2.VideoCapture(video_path)
    
    # Récupération des infos techniques
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # 3. Préparation de l'enregistrement
    out = cv2.VideoWriter(chemin_sortie, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    print(f"🚀 IA : Analyse en cours sur {video_path}...")

    # 4. Boucle image par image
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Détection IA (classes=0 pour 'person')
        results = model.track(frame, persist=True, classes=0, verbose=False)

        # Dessin des boîtes sur l'image
        frame_dessinee = results[0].plot()

        # Sauvegarde de l'image
        out.write(frame_dessinee)

    # 5. Fin
    cap.release()
    out.release()
    print(f"✅ IA : Analyse terminée -> {chemin_sortie}")
    
    return nom_sortie
