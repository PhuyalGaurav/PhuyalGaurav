import os
import requests
import re

lastfm_api_key = os.environ.get('LASTFM_API_KEY')
lastfm_username = os.environ.get('LASTFM_USERNAME')

def get_recently_played():
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={lastfm_username}&api_key={lastfm_api_key}&format=json&limit=1"
    response = requests.get(url)
    data = response.json()
    
    if 'recenttracks' in data and 'track' in data['recenttracks'] and data['recenttracks']['track']:
        track = data['recenttracks']['track'][0]
        
        now_playing = '@attr' in track and 'nowplaying' in track['@attr'] and track['@attr']['nowplaying'] == 'true'
        
        artist = track['artist']['#text']
        song_name = track['name']
        album = track['album']['#text']
        image_url = next((img['#text'] for img in track['image'] if img['size'] == 'large'), '')
        
        status = "Now playing" if now_playing else "Last played"
        
        return {
            'status': status,
            'artist': artist,
            'song_name': song_name,
            'album': album,
            'image_url': image_url
        }
    return None

def update_readme(track_info):
    if not track_info:
        return
    
    try:
        with open('README.md', 'r', encoding='utf-8') as file:
            content = file.read()
        
        start_marker = "<!-- YOUTUBE-MUSIC-START -->"
        end_marker = "<!-- YOUTUBE-MUSIC-END -->"
        
        music_section = f"{start_marker}\n### {track_info['status']} on YouTube Music\n\n"
        if track_info['image_url']:
            music_section += f"[![{track_info['song_name']}]({track_info['image_url']})]({track_info['image_url']})\n\n"
        music_section += f"**{track_info['song_name']}** by {track_info['artist']}\n"
        if track_info['album']:
            music_section += f"Album: {track_info['album']}\n"
        music_section += f"\n{end_marker}"
        
        if start_marker in content and end_marker in content:
            pattern = re.compile(f"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL)
            new_content = pattern.sub(music_section, content)
        else:
            new_content = content + "\n\n" + music_section
        
        with open('README.md', 'w', encoding='utf-8') as file:
            file.write(new_content)
            
        print("README.md updated successfully with recently played music.")
    except Exception as e:
        print(f"Error updating README: {e}")

if __name__ == "__main__":
    track_info = get_recently_played()
    if track_info:
        update_readme(track_info)
    else:
        print("No recently played tracks found or there was an error fetching the data.")
