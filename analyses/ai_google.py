import google.generativeai as genai
import os
import time
from moviepy import VideoFileClip

# Ta clé API
GOOGLE_API_KEY = "AIzaSyBK53P2vcDTExwWV0S3n_x8-NeMECgT0P8"

genai.configure(api_key=GOOGLE_API_KEY)

def analyse_tactique(video_path, debut=None, fin=None):
    print(f"🚀 Préparation IA sur : {video_path}")
    
    # Nom unique pour éviter les conflits
    path_temp = video_path + f"_temp_ia_{int(time.time())}.mp4"
    
    try:
        # --- 1. PRÉPARATION ---
        with VideoFileClip(video_path) as clip:
            start = debut if debut is not None else 0
            if fin is not None:
                end = fin
            else:
                end = min(clip.duration, 90) # Max 90s
            
            # Sécurité durée
            end = min(end, clip.duration)
            
            # Coupe et compression
            clip_court = clip.subclipped(start, end)
            print(f"... Optimisation (480p) de {start}s à {end}s ...")
            
            clip_court.resized(height=480).write_videofile(
                path_temp, codec="libx264", audio=False, preset="ultrafast", logger=None
            )
            
        # --- 2. ENVOI GOOGLE ---
        print(f"🚀 Envoi vers Gemini...")
        video_file = genai.upload_file(path=path_temp)
        
        while video_file.state.name == "PROCESSING":
            time.sleep(1)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED": 
            return "❌ Erreur : Google n'a pas réussi à lire la vidéo."

        # --- 3. COACH (RETOUR AU MODÈLE FIABLE 2.0) ---
        print("🧠 Analyse en cours (Gemini 2.0 Flash)...")
        # C'est ici qu'on corrige l'erreur 429
        model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")
        
        prompt = """
        Tu es un analyste sportif expert (football/soccer).
        Analyse ce clip. Fais un rapport structuré pour un coach :
        
        🎬 **RÉSUMÉ :** (1 phrase)
        ✅ **POINTS FORTS :** (Ce qui est bien réalisé)
        ⚠️ **À CORRIGER :** (Erreurs techniques/tactiques)
        💡 **CONSEIL :** (Conseil pour le joueur)
        """

        response = model.generate_content([video_file, prompt])
        
        # --- 4. NETTOYAGE ---
        genai.delete_file(video_file.name)
        if os.path.exists(path_temp): os.remove(path_temp) 
        
        return response.text

    except Exception as e:
        if os.path.exists(path_temp): os.remove(path_temp)
        return f"Erreur technique : {str(e)}"
    
    