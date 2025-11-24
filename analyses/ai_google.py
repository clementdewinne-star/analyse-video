import google.generativeai as genai
import os
import time
import requests
from moviepy import VideoFileClip

# ⚠️ TA CLÉ GOOGLE ICI
GOOGLE_API_KEY = "AIzaSyBK53P2vcDTExwWV0S3n_x8-NeMECgT0P8"

genai.configure(api_key=GOOGLE_API_KEY)

def analyse_tactique(video_url, debut=None, fin=None):
    print(f"🚀 IA Tactique sur : {video_url}")
    ts = int(time.time())
    path_dl = f"temp_dl_{ts}.mp4"
    path_comp = f"temp_comp_{ts}.mp4"
    
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

        # 2. Coupe & Compression
        with VideoFileClip(source) as clip:
            start = debut if debut is not None else 0
            if fin is not None: end = fin
            else: end = min(clip.duration, 90)
            end = min(end, clip.duration)
            
            clip.subclipped(start, end).resized(height=480).write_videofile(
                path_comp, codec="libx264", audio=False, preset="ultrafast", logger=None
            )
            
        # 3. Google
        print("... Envoi Gemini ...")
        vfile = genai.upload_file(path=path_comp)
        while vfile.state.name == "PROCESSING":
            time.sleep(1)
            vfile = genai.get_file(vfile.name)

        if vfile.state.name == "FAILED": return "Erreur lecture vidéo."

        # 4. Prompt
        model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")
        prompt = """
        Analyste expert foot. Analyse ce clip. Rapport structuré :
        🎬 **RÉSUMÉ**
        ✅ **POINTS FORTS**
        ⚠️ **À CORRIGER**
        💡 **CONSEIL**
        Utilise des émojis.
        """
        resp = model.generate_content([vfile, prompt])
        
        # Nettoyage
        genai.delete_file(vfile.name)
        if os.path.exists(path_dl): os.remove(path_dl)
        if os.path.exists(path_comp): os.remove(path_comp)
        
        return resp.text

    except Exception as e:
        return f"Erreur technique : {str(e)}"
    
    