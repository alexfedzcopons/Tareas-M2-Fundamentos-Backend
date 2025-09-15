from django.contrib import admin
from .models import Usuario, MusicPreference

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'age', 'created_at']

@admin.register(MusicPreference)
class MusicPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'type', 'added_at']