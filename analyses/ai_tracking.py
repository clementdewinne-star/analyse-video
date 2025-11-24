import cv2
from ultralytics import YOLO
import os
import requests
import time
from django.conf import settings

model = YOLO('yolov8n.pt')

def generer_tracking_spotlight(video_url, video_id):
    print(f"🔦 Spotlight sur : {video_url}")
    ts = int(time.time())
    path_dl = f"temp_spot_dl_{ts}.mp4"
    nom_sortie = f"Spotlight_{video_id}_{ts}.mp4"
    dossier = os.path.join(settings.MEDIA_ROOT, 'clips')
    os.makedirs(dossier, exist_ok=True)
    path_out = os.path.join(dossier, nom_sortie)

    try:
        # 1. Téléchargement
        if video_url.startswith('http'):
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                with open(path_dl, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            source = path_dl
        else:
            source = video_url.lstrip('/')

        # 2. Traitement
        cap = cv2.VideoCapture(source)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        out = cv2.VideoWriter(path_out, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            frame_count += 1
            
            results = model.track(frame, persist=True, classes=0, verbose=False)
            overlay = frame.copy()
            
            if results[0].boxes is not None:
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx, by = int((x1+x2)/2), int(y2)
                    rx = int((x2-x1)/1.5)
                    ry = int(rx/3)
                    cv2.ellipse(overlay, (cx, by), (rx, ry), 0, 0, 360, (255, 255, 100), -1)

            cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
            out.write(frame)

        cap.release()
        out.release()
        if os.path.exists(path_dl): os.remove(path_dl)
        
        return nom_sortie

    except Exception as e:
        print(f"Erreur YOLO: {e}")
        return None
    