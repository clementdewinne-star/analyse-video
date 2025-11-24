import cv2
from ultralytics import YOLO
import os
import requests
import cloudinary
import cloudinary.uploader
import time
from django.conf import settings

# 1. CONFIGURATION CLOUDINARY OBLIGATOIRE
# Le script a besoin de ses propres clés pour fonctionner
cloudinary.config(
    cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
    api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
)

model = YOLO('yolov8n.pt')

def generer_tracking_spotlight(video_url, video_id):
    print(f"🔦 Démarrage Spotlight sur : {video_url}")
    
    ts = int(time.time())
    path_dl = f"temp_in_{video_id}_{ts}.mp4"
    path_out = f"temp_out_{video_id}_{ts}.mp4"

    try:
        # 2. TÉLÉCHARGEMENT OBLIGATOIRE
        # Sur Render, le fichier n'est PAS sur le disque. Il faut le télécharger.
        # Si l'url commence par /media, c'est qu'il manque le début (https://res.cloudinary...)
        
        url_a_telecharger = video_url
        
        # Correction automatique de l'URL si elle est relative
        if not video_url.startswith('http'):
            # On reconstruit l'URL Cloudinary si Django nous donne un chemin relatif
            cloud_name = settings.CLOUDINARY_STORAGE['CLOUD_NAME']
            url_a_telecharger = f"https://res.cloudinary.com/{cloud_name}/{video_url}"
            # Nettoyage des doubles slashs éventuels au début
            if video_url.startswith('/'):
                url_a_telecharger = f"https://res.cloudinary.com/{cloud_name}{video_url}"

        print(f"... Téléchargement depuis : {url_a_telecharger}")
        
        with requests.get(url_a_telecharger, stream=True) as r:
            if r.status_code == 200:
                with open(path_dl, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            else:
                print(f"❌ Erreur téléchargement : Code {r.status_code}")
                return None

        # 3. TRAITEMENT OPENCV
        cap = cv2.VideoCapture(path_dl)
        
        # Si OpenCV n'arrive pas à ouvrir le fichier téléchargé
        if not cap.isOpened():
            print("❌ Erreur : Impossible d'ouvrir la vidéo téléchargée.")
            return None

        w_orig = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h_orig = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Facteur de réduction (pour aller vite sur serveur gratuit)
        scale = 640 / w_orig if w_orig > 640 else 1.0
        w_new, h_new = int(w_orig * scale), int(h_orig * scale)
        
        out = cv2.VideoWriter(path_out, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w_new, h_new))

        frame_count = 0
        max_frames = int(fps * 10) # 10 secondes max

        print(f"Traitement de {max_frames} images...")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame_count >= max_frames: break
            
            frame_count += 1
            
            if scale != 1.0:
                frame = cv2.resize(frame, (w_new, h_new))

            results = model.track(frame, persist=True, classes=0, verbose=False)
            overlay = frame.copy()
            
            if results[0].boxes is not None:
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx, by = int((x1+x2)/2), int(y2)
                    rx = int((x2-x1)/1.2)
                    ry = int(rx/4)
                    cv2.ellipse(overlay, (cx, by), (rx, ry), 0, 0, 360, (255, 255, 255), -1)

            cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
            out.write(frame)

        cap.release()
        out.release()

        # 4. UPLOAD RESULTAT VERS CLOUDINARY
        print("☁️ Envoi du résultat Cloudinary...")
        res = cloudinary.uploader.upload(
            path_out, 
            resource_type="video",
            public_id=f"analyses/spot_light_{video_id}_{ts}"
        )
        
        # Nettoyage
        if os.path.exists(path_dl): os.remove(path_dl)
        if os.path.exists(path_out): os.remove(path_out)
        
        return res.get('secure_url')

    except Exception as e:
        print(f"ERREUR CRITIQUE : {e}")
        if os.path.exists(path_dl): os.remove(path_dl)
        if os.path.exists(path_out): os.remove(path_out)
        return None
    
    