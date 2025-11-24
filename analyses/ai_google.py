import google.generativeai as genai
import os
import time
import requests 
from moviepy import VideoFileClip

# Ta clé API Google (Remets la tienne si différente)
GOOGLE_API_KEY = "AIzaSyBK53P2vcDTExwWV0S3n_x8-NeMECgT0P8"

genai.configure(api_key=GOOGLE_API_KEY)

def download_from_url(url, local_filename):
    """Télécharge un fichier depuis une URL vers le disque local temporaire"""
    print(f"... Téléchargement Cloudinary vers Render ...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename
    except Exception as e:
        print(f"Erreur téléchargement: {e}")
        return None

def analyse_tactique(video_url, debut=None, fin=None):
    print(f"🚀 Démarrage IA...")
    
    # Noms de fichiers temporaires
    ts = int(time.time())
    path_download = f"temp_dl_{ts}.mp4"
    path_compressed = f"temp_comp_{ts}.mp4"
    
    try:
        # --- 1. RÉCUPÉRATION DU FICHIER ---
        if video_url.startswith('http'):
            # Si c'est une URL (Cloudinary), on télécharge
            if not download_from_url(video_url, path_download):
                return "❌ Erreur : Impossible de télécharger la vidéo depuis Cloudinary."
            source_file = path_download
        else:
            # Cas local (rare en prod)
            if video_url.startswith('/'): video_url = video_url[1:]
            source_file = video_url

        # --- 2. TRAITEMENT & COMPRESSION ---
        with VideoFileClip(source_file) as clip:
            start = debut if debut is not None else 0
            if fin is not None: end = fin
            else: end = min(clip.duration, 90)
            
            end = min(end, clip.duration)
            clip_court = clip.subclipped(start, end)
            
            print(f"... Optimisation (480p) ...")
            clip_court.resized(height=480).write_videofile(
                path_compressed, codec="libx264", audio=False, preset="ultrafast", logger=None
            )
            
        # --- 3. ENVOI GOOGLE ---
        print(f"🚀 Envoi vers Gemini...")
        video_file = genai.upload_file(path=path_compressed)
        
        while video_file.state.name == "PROCESSING":
            time.sleep(1)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED": return "❌ Erreur : Google a rejeté la vidéo."

        # --- 4. PROMPT ---
        print("🧠 Analyse en cours...")
        model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")
        prompt = """
        Analyste expert foot. Analyse ce clip.
        Rapport structuré :
        🎬 **RÉSUMÉ**
        ✅ **POINTS FORTS**
        ⚠️ **À CORRIGER**
        💡 **CONSEIL**
        Utilise des émojis.
        """
        response = model.generate_content([video_file, prompt])
        
        # --- 5. NETTOYAGE ---
        genai.delete_file(video_file.name)
        if os.path.exists(path_download): os.remove(path_download)
        if os.path.exists(path_compressed): os.remove(path_compressed)
        
        return response.text

    except Exception as e:
        if os.path.exists(path_download): os.remove(path_download)
        if os.path.exists(path_compressed): os.remove(path_compressed)
        return f"Erreur technique : {str(e)}"
    
    