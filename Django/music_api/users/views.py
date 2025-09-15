from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Usuario, MusicPreference
from django.conf import settings
import requests
import base64

# ============== FUNCIONES DE SPOTIFY ==============

def get_spotify_token():
    """Obtener token de Spotify - igual que en FastAPI"""
    client_id = settings.SPOTIFY_CLIENT_ID
    client_secret = settings.SPOTIFY_CLIENT_SECRET
    
    if not client_id or not client_secret:
        return None
    
    client_credentials = f"{client_id}:{client_secret}"
    client_credentials_b64 = base64.b64encode(client_credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {client_credentials_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {"grant_type": "client_credentials"}
    
    try:
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers=headers,
            data=data
        )
        if response.status_code == 200:
            return response.json()["access_token"]
    except:
        pass
    return None

def search_spotify(query, search_type="track", limit=10):
    """Buscar en Spotify - igual que en FastAPI"""
    token = get_spotify_token()
    if not token:
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": query, "type": search_type, "limit": limit}
    
    try:
        response = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params=params
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

# ============== VIEWS EXISTENTES ==============

@api_view(['GET'])
def hello(request):
    return Response({"message": "Hola desde Django"})

@api_view(['GET'])
def health(request):
    return Response({"status": "OK", "framework": "Django"})

@api_view(['GET'])
def users_list(request):
    """Listar todos los usuarios"""
    usuarios = Usuario.objects.all()
    data = []
    for usuario in usuarios:
        data.append({
            'id': usuario.id,
            'name': usuario.name,
            'email': usuario.email,
            'age': usuario.age
        })
    return Response(data)

@api_view(['POST'])
def users_create(request):
    """Crear un usuario nuevo"""
    name = request.data.get('name')
    email = request.data.get('email')
    age = request.data.get('age')
    
    if not all([name, email, age]):
        return Response({"error": "Faltan datos"}, status=400)
    
    usuario = Usuario.objects.create(
        name=name,
        email=email,
        age=age
    )
    
    return Response({
        'id': usuario.id,
        'name': usuario.name,
        'email': usuario.email,
        'age': usuario.age
    })

@api_view(['GET'])
def preferences_list(request):
    """Listar todas las preferencias musicales"""
    preferences = MusicPreference.objects.all()
    data = []
    for pref in preferences:
        data.append({
            'id': pref.id,
            'user_id': pref.user.id,
            'user_name': pref.user.name,
            'spotify_id': pref.spotify_id,
            'name': pref.name,
            'type': pref.type,
            'added_at': pref.added_at
        })
    return Response(data)

@api_view(['GET'])
def user_preferences(request, user_id):
    """Obtener preferencias de un usuario específico"""
    try:
        usuario = Usuario.objects.get(id=user_id)
        preferences = MusicPreference.objects.filter(user=usuario)
        data = []
        for pref in preferences:
            data.append({
                'id': pref.id,
                'spotify_id': pref.spotify_id,
                'name': pref.name,
                'type': pref.type,
                'added_at': pref.added_at
            })
        return Response(data)
    except Usuario.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=404)

# ============== NUEVAS VIEWS DE SPOTIFY ==============

@api_view(['GET'])
def spotify_test(request):
    """Probar conexión con Spotify"""
    token = get_spotify_token()
    if token:
        return Response({
            "status": "success",
            "message": "Conexión con Spotify OK",
            "token_preview": token[:20] + "..."
        })
    else:
        return Response({
            "status": "error",
            "message": "No se pudo conectar con Spotify"
        }, status=400)

@api_view(['GET'])
def spotify_search_tracks(request):
    """Buscar canciones en Spotify"""
    query = request.GET.get('q')
    if not query:
        return Response({"error": "Falta parámetro 'q'"}, status=400)
    
    results = search_spotify(query, "track", 10)
    if not results:
        return Response({"error": "Error conectando con Spotify"}, status=500)
    
    # Simplificar respuesta como en FastAPI
    simplified_tracks = []
    for track in results.get("tracks", {}).get("items", []):
        simplified_track = {
            "spotify_id": track["id"],
            "name": track["name"],
            "artists": [artist["name"] for artist in track["artists"]],
            "album": track["album"]["name"],
            "external_url": track["external_urls"]["spotify"]
        }
        simplified_tracks.append(simplified_track)
    
    return Response({
        "query": query,
        "total": len(simplified_tracks),
        "tracks": simplified_tracks
    })

@api_view(['GET'])
def spotify_search_artists(request):
    """Buscar artistas en Spotify"""
    query = request.GET.get('q')
    if not query:
        return Response({"error": "Falta parámetro 'q'"}, status=400)
    
    results = search_spotify(query, "artist", 10)
    if not results:
        return Response({"error": "Error conectando con Spotify"}, status=500)
    
    # Simplificar respuesta como en FastAPI
    simplified_artists = []
    for artist in results.get("artists", {}).get("items", []):
        simplified_artist = {
            "spotify_id": artist["id"],
            "name": artist["name"],
            "genres": artist["genres"],
            "followers": artist["followers"]["total"],
            "external_url": artist["external_urls"]["spotify"]
        }
        simplified_artists.append(simplified_artist)
    
    return Response({
        "query": query,
        "total": len(simplified_artists),
        "artists": simplified_artists
    })