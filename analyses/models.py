from django.db import models

class Video(models.Model):
    titre = models.CharField(max_length=100)
    fichier_video = models.FileField(upload_to='videos/')
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre

class Sequence(models.Model):
    # Regarde ici : il y a un espace (Tabulation) avant le mot "video"
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='sequences')
    label = models.CharField(max_length=100)
    temps_debut = models.FloatField()
    temps_fin = models.FloatField()
    
    def __str__(self):
        return f"{self.label} ({self.temps_debut}s)"