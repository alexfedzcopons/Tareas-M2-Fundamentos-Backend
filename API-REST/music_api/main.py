
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

import requests
import os
from dotenv import load_dotenv
import base64

load_dotenv()


# Configuración FastAPI y CORS

app = FastAPI(
    title="Spotify API",
    description="API para gestionar usuarios y sus preferencias musicales con Spotify",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Modelos Pydantic Usuarios

class UserCreate(BaseModel):
    name: str
    email: str
    age: int

class User(BaseModel):
    id: int
    name: str
    email: str
    age: int

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    


# Modelos Pydantic Preferencias
# Para la música es necesario buscar primero y anotar ID, se distingue entre canción o artista porque pueden compartir id

class MusicPreferenceCreate(BaseModel):
    spotify_id: str
    name: str
    type: str  # "song" o "artist"

class MusicPreference(BaseModel):
    id: int
    user_id: int
    spotify_id: str  # ID de Spotify
    name: str        # Nombre de la canción o artista
    type: str        # "song" o "artist"



# Guardar Usuarios y Preferencias musicales en listas y darles id

users_db = []  
next_user_id = 1 

music_preferences_db = []  
next_preference_id = 1     



# Configuración Spotify, están en el archivo .env y luego se debería añadir .env a gitignore para no subir las claves a GitHub

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

spotify_access_token = None



# Funciones de autenticación de Spotify

def get_spotify_token():
    global spotify_access_token
    
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise HTTPException(
            status_code= 500, 
            detail="Credenciales de Spotify no configuradas. Revisa las variables de entorno."
        )
    
    client_credentials = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    client_credentials_b64 = base64.b64encode(client_credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {client_credentials_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "client_credentials"
    }
    
    try:
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            token_data = response.json()
            spotify_access_token = token_data["access_token"]
            return spotify_access_token
        else:
            raise HTTPException(
                status_code= 500,
                detail=f"Error al obtener token de Spotify: {response.status_code}"
            )
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code= 500,
            detail=f"Error de conexión con Spotify: {str(e)}"
        )


def search_spotify(query: str, search_type: str = "track", limit: int = 10):
    token = get_spotify_token()
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    params = {
        "q": query,
        "type": search_type,  # track, artist, album
        "limit": limit
    }
    
    try:
        response = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error en búsqueda de Spotify: {response.text}"
            )
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code= 500,
            detail=f"Error de conexión con Spotify: {str(e)}"
        )



# Endpoints de Diagnóstico

@app.get("/")
async def root():
    return {
        "message": "Bienvenido a la API de Spotify",
    }

@app.get("/health")
async def health_check():
    return {"status": "OK", "message": "API funcionando correctamente"}



# CRUD de Usuarios

@app.post("/users", response_model= User)
async def create_user(user_data: UserCreate):
    global next_user_id
    
    for existing_user in users_db:
        if existing_user["email"] == user_data.email:
            raise HTTPException(status_code= 400, detail="El email ya existe")
    
    new_user = {
        "id": next_user_id,
        "name": user_data.name,
        "email": user_data.email,
        "age": user_data.age,
    }
    
    users_db.append(new_user)
    next_user_id += 1
    
    return new_user


@app.get("/users", response_model= List[User])
async def get_all_users():
    return users_db


@app.get("/users/{user_id}", response_model= User)
async def get_user_by_id(user_id: int):
    for user in users_db:
        if user["id"] == user_id:
            return user
    
    raise HTTPException(status_code= 404, detail="Usuario no encontrado")


@app.put("/users/{user_id}", response_model= User)
async def update_user(user_id: int, user_update: UserUpdate):
    user_index = None
    
    for i, user in enumerate(users_db):
        if user["id"] == user_id:
            user_index = i
            break
    
    if user_index is None:
        raise HTTPException(status_code= 404, detail="Usuario no existe")
    
    if user_update.email:
        for user in users_db:
            if user["email"] == user_update.email and user["id"] != user_id:
                raise HTTPException(status_code= 400, detail="El email ya existe")
    
    user_data = users_db[user_index]
    if user_update.name is not None:
        user_data["name"] = user_update.name
    if user_update.email is not None:
        user_data["email"] = user_update.email
    if user_update.age is not None:
        user_data["age"] = user_update.age
    
    return user_data


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    for i, user in enumerate(users_db):
        if user["id"] == user_id:
            deleted_user = users_db.pop(i)
            return {"message": f"Usuario {deleted_user['name']} eliminado correctamente"}
    
    raise HTTPException(status_code= 404, detail="Usuario no existe")




# CRUD de Preferencias Musicales

@app.post("/users/{user_id}/preferences", response_model= MusicPreference)
async def add_music_preference(user_id: int, preference_data: MusicPreferenceCreate):
    global next_preference_id
    
    user_exists = False
    for user in users_db:
        if user["id"] == user_id:
            user_exists = True
            break
    
    if not user_exists:
        raise HTTPException(status_code= 404, detail="Usuario no existe")
    
    for pref in music_preferences_db:
        if pref["user_id"] == user_id and pref["spotify_id"] == preference_data.spotify_id:
            raise HTTPException(status_code= 400, detail="Esta preferencia ya existe")
    
    new_preference = {
        "id": next_preference_id,
        "user_id": user_id,
        "spotify_id": preference_data.spotify_id,
        "name": preference_data.name,
        "type": preference_data.type,
    }
    
    music_preferences_db.append(new_preference)
    next_preference_id += 1
    
    return new_preference

@app.get("/users/{user_id}/preferences", response_model= List[MusicPreference])
async def get_user_preferences(user_id: int):
    user_exists = False
    
    for user in users_db:
        if user["id"] == user_id:
            user_exists = True
            break
    
    if not user_exists:
        raise HTTPException(status_code= 404, detail="Usuario no existe")
    
    user_preferences = []
    for pref in music_preferences_db:
        if pref["user_id"] == user_id:
            user_preferences.append(pref)
    
    return user_preferences

@app.delete("/preferences/{preference_id}")
async def delete_music_preference(preference_id: int):
    for i, pref in enumerate(music_preferences_db):
        if pref["id"] == preference_id:
            deleted_pref = music_preferences_db.pop(i)
            return {"message": f"Preferencia '{deleted_pref['name']}' eliminada"}
    
    raise HTTPException(status_code= 404, detail="Preferencia no existe")



# Endpoints de Spotify

@app.get("/spotify/test")
async def test_spotify_connection():
    try:
        token = get_spotify_token()
        return {
            "status": "success",
            "message": "Conexión con Spotify establecida",
            "token_preview": token[:20] + "..." if token else None
        }
    except HTTPException as e:
        return {
            "status": "error",
            "message": e.detail
        }


@app.get("/spotify/search/tracks")
async def search_tracks(q: str, limit: int = 10):
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code= 400, detail="La búsqueda debe tener al menos 2 caracteres")
    
    results = search_spotify(q, "track", limit)
    
    # Para reducir la cantidad de datos que devuelve
    simplified_tracks = []
    for track in results.get("tracks", {}).get("items", []):
        simplified_track = {
            "spotify_id": track["id"],
            "name": track["name"],
            "artists": [artist["name"] for artist in track["artists"]],
            "album": track["album"]["name"],
        }
        simplified_tracks.append(simplified_track)
    
    return {
        "query": q,
        "total": len(simplified_tracks),
        "tracks": simplified_tracks
    }


@app.get("/spotify/search/artists")
async def search_artists(q: str, limit: int = 10):
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code= 400, detail="La búsqueda debe tener al menos 2 caracteres")
    
    results = search_spotify(q, "artist", limit)
    
    # Para reducir la cantidad de datos que devuelve
    simplified_artists = []
    for artist in results.get("artists", {}).get("items", []):
        simplified_artist = {
            "spotify_id": artist["id"],
            "name": artist["name"],
            "genres": artist["genres"],
            "followers": artist["followers"]["total"],
            "popularity": artist["popularity"],
        }
        simplified_artists.append(simplified_artist)
    
    return {
        "query": q,
        "total": len(simplified_artists),
        "artists": simplified_artists
    }


# Para ejecutar con: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)