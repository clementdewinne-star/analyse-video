import google.generativeai as genai
import os
import time
import requests # Pour télécharger depuis le cloud
from moviepy import VideoFileClip

# Ta clé API Google
GOOGLE_API_KEY = "AIzaSyBK53P2vcDTExwWV0S3n_x8-NeMECgT0P8"

genai.configure(api_key=GOOGLE_API_KEY)

def download_file(url, local_filename):
    """Télécharge un fichier depuis une URL (Cloudinary) vers le disque local"""
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename

def analyse_tactique(video_url, debut=None, fin=None):
    print(f"🚀 Démarrage IA sur URL Cloud...")
    
    # Nom des fichiers temporaires
    ts = int(time.time())
    path_downloaded = f"temp_download_{ts}.mp4"
    path_compressed = f"temp_compressed_{ts}.mp4"
    
    try:
        # 1. TÉLÉCHARGEMENT DEPUIS CLOUDINARY
        print("... Téléchargement de la vidéo depuis le Cloud ...")
        # Si c'est une URL (commence par http), on télécharge. Sinon on prend tel quel.
        if video_url.startswith('http'):
            download_file(video_url, path_downloaded)
            video_source = path_downloaded
        else:
            video_source = video_url # Cas local

        # 2. TRAITEMENT MOVIEPY
        with VideoFileClip(video_source) as clip:
            start = debut if debut is not None else 0
            if fin is not None: end = fin
            else: end = min(clip.duration, 90)
            
            end = min(end, clip.duration)
            clip_court = clip.subclipped(start, end)
            
            print(f"... Optimisation (480p) ...")
            clip_court.resized(height=480).write_videofile(
                path_compressed, codec="libx264", audio=False, preset="ultrafast", logger=None
            )
            
        # 3. ENVOI GOOGLE
        print(f"🚀 Envoi vers Gemini...")
        video_file = genai.upload_file(path=path_compressed)
        
        while video_file.state.name == "PROCESSING":
            time.sleep(1)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED": return "❌ Erreur Google."

        # 4. ANALYSE
        print("🧠 Analyse en cours...")
        model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")
        prompt = """
        Analyste sportif expert (foot). Analyse ce clip.
        Format :
        🎬 **RÉSUMÉ**
        ✅ **POINTS FORTS**
        ⚠️ **À CORRIGER**
        💡 **CONSEIL**
        """
        response = model.generate_content([video_file, prompt])
        
        # 5. NETTOYAGE
        genai.delete_file(video_file.name)
        if os.path.exists(path_downloaded): os.remove(path_downloaded)
        if os.path.exists(path_compressed): os.remove(path_compressed)
        
        return response.text

    except Exception as e:
        # Nettoyage en cas d'erreur
        if os.path.exists(path_downloaded): os.remove(path_downloaded)
        if os.path.exists(path_compressed): os.remove(path_compressed)
        return f"Erreur technique : {str(e)}"
    
    