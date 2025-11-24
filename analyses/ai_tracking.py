import cv2
from ultralytics import YOLO
import os
import requests
import cloudinary.uploader
import time
from django.conf import settings

# On utilise le modèle le plus léger possible
model = YOLO('yolov8n.pt')

def generer_tracking_spotlight(video_url, video_id):
    print(f"🔦 Démarrage Spotlight Light sur : {video_url}")
    
    ts = int(time.time())
    path_dl = f"temp_in_{video_id}_{ts}.mp4"
    path_out = f"temp_out_{video_id}_{ts}.mp4"

    try:
        # 1. TÉLÉCHARGEMENT
        if video_url.startswith('http'):
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                with open(path_dl, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            source = path_dl
        else:
            source = video_url.lstrip('/')

        # 2. TRAITEMENT (Optimisé pour serveur gratuit)
        cap = cv2.VideoCapture(source)
        
        # On réduit la résolution pour accélérer le calcul (640px max)
        w_orig = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h_orig = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Facteur de réduction
        scale = 640 / w_orig if w_orig > 640 else 1.0
        w_new, h_new = int(w_orig * scale), int(h_orig * scale)
        
        out = cv2.VideoWriter(path_out, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w_new, h_new))

        frame_count = 0
        max_frames = int(fps * 10) # ⚠️ LIMITE : 10 Secondes MAX pour ne pas planter

        print(f"Traitement de {max_frames} images (10s)...")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame_count >= max_frames: break
            
            frame_count += 1
            
            # Redimensionnement (Moins de pixels = Plus vite)
            if scale != 1.0:
                frame = cv2.resize(frame, (w_new, h_new))

            # Tracking IA
            results = model.track(frame, persist=True, classes=0, verbose=False)
            overlay = frame.copy()
            
            if results[0].boxes is not None:
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Projecteur
                    cx, by = int((x1+x2)/2), int(y2)
                    rx = int((x2-x1)/1.2)
                    ry = int(rx/4)
                    cv2.ellipse(overlay, (cx, by), (rx, ry), 0, 0, 360, (255, 255, 255), -1)

            # Fusion
            cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
            out.write(frame)

        cap.release()
        out.release()

        # 3. UPLOAD CLOUDINARY
        print("☁️ Envoi Cloudinary...")
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
    
    