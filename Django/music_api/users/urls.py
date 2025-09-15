from django.urls import path
from . import views

urlpatterns = [
    path('hello/', views.hello, name='hello'),
    path('health/', views.health, name='health'),
    path('users/', views.users_list, name='users_list'),
    path('users/create/', views.users_create, name='users_create'),
    path('preferences/', views.preferences_list, name='preferences_list'),
    path('users/<int:user_id>/preferences/', views.user_preferences, name='user_preferences'),
    
    # Endpoints de Spotify
    path('spotify/test/', views.spotify_test, name='spotify_test'),
    path('spotify/search/tracks/', views.spotify_search_tracks, name='spotify_search_tracks'),
    path('spotify/search/artists/', views.spotify_search_artists, name='spotify_search_artists'),
]