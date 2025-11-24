import cv2
from ultralytics import YOLO
import os
import requests
import cloudinary.uploader # Pour envoyer sur le cloud
from django.conf import settings

# Modèle IA
model = YOLO('yolov8n.pt')

def generer_tracking_spotlight(video_url, video_id):
    print(f"🔦 Démarrage Spotlight...")
    
    # Noms de fichiers
    filename = f"spotlight_{video_id}.mp4"
    path_dl = f"temp_in_{video_id}.mp4"
    path_out = f"temp_out_{video_id}.mp4"

    try:
        # 1. TÉLÉCHARGEMENT DE LA SOURCE
        if video_url.startswith('http'):
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                with open(path_dl, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            source = path_dl
        else:
            source = video_url.lstrip('/')

        # 2. TRAITEMENT VIDÉO (YOLO)
        cap = cv2.VideoCapture(source)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # On écrit le résultat
        out = cv2.VideoWriter(path_out, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            # Tracking
            results = model.track(frame, persist=True, classes=0, verbose=False)
            overlay = frame.copy()
            
            if results[0].boxes is not None:
                for box in results[0].boxes:
                    # Coordonnées
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx, by = int((x1+x2)/2), int(y2) # Centre pieds
                    
                    # Dessin du Projecteur (Ellipse au sol)
                    rx = int((x2-x1)/1.2)
                    ry = int(rx/4)
                    
                    # Cercle Blanc Semi-Transparent au sol
                    cv2.ellipse(overlay, (cx, by), (rx, ry), 0, 0, 360, (255, 255, 255), -1)
                    
                    # Optionnel : Cercle coloré autour du joueur
                    # cv2.ellipse(overlay, (cx, by), (rx+10, ry+10), 0, 0, 360, (0, 255, 255), 2)

            # Fusion transparence (Effet lumière)
            cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
            out.write(frame)

        cap.release()
        out.release()

        # 3. UPLOAD VERS CLOUDINARY
        print("☁️ Envoi du résultat vers le Cloud...")
        upload_result = cloudinary.uploader.upload(
            path_out, 
            resource_type="video",
            public_id=f"analyses/spotlight_{video_id}_{int(time.time())}"
        )
        
        # Nettoyage
        if os.path.exists(path_dl): os.remove(path_dl)
        if os.path.exists(path_out): os.remove(path_out)
        
        # On retourne l'URL sécurisée du fichier en ligne
        return upload_result.get('secure_url')

    except Exception as e:
        print(f"Erreur : {e}")
        # Nettoyage secours
        if os.path.exists(path_dl): os.remove(path_dl)
        if os.path.exists(path_out): os.remove(path_out)
        return None
import time # J'avais oublié l'import time

