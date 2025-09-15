from django.db import models

class Usuario(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    age = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class MusicPreference(models.Model):
    user = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    spotify_id = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=[('song', 'Song'), ('artist', 'Artist')])
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.name}"