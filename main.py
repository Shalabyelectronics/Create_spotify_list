import requests
from bs4 import BeautifulSoup
from datetime import datetime
import spotipy
import os
from spotipy.oauth2 import SpotifyOAuth
from tqdm import tqdm
from pprint import pprint

URL = "https://www.billboard.com/charts/hot-100/"
SPOTIPY_CLIENT_ID = os.environ.get("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = "http://example.com"


def pick_a_date():
    date = datetime(year=int(input("which year : ")), month=int(input("which month : ")),
                    day=int(input("which day : ")))
    return date.strftime("%Y-%m-%d")


def request_data(format_date):
    response = requests.get(f"{URL}/{format_date}")
    file_path = f"playlists_files/{format_date}-music.html"
    if os.path.isdir("playlists_files"):
        with open(file_path, 'w') as music_page:
            music_page.write(response.text)
            return file_path
    else:
        os.mkdir("playlists_files")
        with open(f"playlists_files/{format_date}-music.html", 'w') as music_page:
            music_page.write(response.text)
            return file_path


def playlist_name(file_path):
    indexes = []
    for i in file_path:
        if i == '/' or i == '.':
            indexes.append(file_path.index(i))
    return file_path[indexes[0] + 1: indexes[1]]


def scrap_html_page(html_page_path):
    with open(html_page_path) as html_file:
        web_data = html_file.read()
    soup = BeautifulSoup(web_data, "html.parser")
    all_music = soup.find_all(name="h3", id="title-of-a-story", class_="a-no-trucate")
    all_singer = soup.find_all(name="span", class_="a-no-trucate")
    all_music_name = [music.getText().strip() for music in tqdm(all_music)]
    all_singer_name = [singer.getText().strip() for singer in tqdm(all_singer)]
    songs_artists = [{'song': all_music_name[i], 'artist': all_singer_name[i]} for i in tqdm(range(len(all_music_name)))]
    return songs_artists

def create_spotify_playlist(play_list_name: str, date: str, songs: list):
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope="playlist-modify-private",
            redirect_uri=SPOTIPY_REDIRECT_URI,
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            show_dialog=True,
            cache_path="user_token/token.txt"
        )
    )
    year = date.split()[-1]
    user_id = sp.current_user()['id']
    song_uris = []
    songs_added = []
    songs_skipped = []
    for i in tqdm(songs):
        result = sp.search(q=f"track:{i['song']} artist:{i['artist']}", type='track')
        try:
            uri = result['tracks']['items'][0]['uri']
            song_uris.append(uri)
        except IndexError:
            songs_skipped.append(f"{i['song']} by {i['artist']} doesn't exist in Spotify. Skipped.")
        else:
            songs_added.append(f"{i['song']} by {i['artist']} doesn't exist in Spotify. Skipped.")

    print(f"There are {len(songs_skipped)} was skipped")
    pprint(songs_skipped)
    print(f"There are {len(song_uris)} are added.")
    pprint(songs_added)
    create_playlist = sp.user_playlist_create(user=user_id, public=False, name=f"Music from {year}",
                                              description=f"This {play_list_name}"
                                                          f"playlist includes songs from {year}")

    sp.playlist_add_items(playlist_id=create_playlist['id'], items=song_uris)
    print(f"Your playlist {play_list_name} created successfully")


def start_app():
    print("Welcome to Spotify create lists app ....")
    print("Please type from which year you want to create your playlist songs\n")
    date = pick_a_date()
    print("please Wait")
    file_path = request_data(date)
    play_list_name = playlist_name(file_path)
    artists_songs_dict = scrap_html_page(file_path)
    create_spotify_playlist(play_list_name, date, artists_songs_dict)


start_app()