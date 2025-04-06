import os
import requests
import re
import json
import sys
import traceback

# Last.fm credentials
lastfm_api_key = os.environ.get('LASTFM_API_KEY')
lastfm_username = os.environ.get('LASTFM_USERNAME')

# Discord webhook for logging
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1358522852999041215/VU3mbXSm0oiQ1jcUhETS8J5kGan30RBuBqQhkuPh0BC66gFwbhOFs4pGqzGrDlRvBm_x"

def send_discord_message(content, title=None, success=True):
    """Send a message to Discord webhook"""
    try:
        color = 0x00FF00 if success else 0xFF0000  # Green for success, Red for errors
        payload = {
            "embeds": [
                {
                    "title": title or ("Music Update Success" if success else "Music Update Error"),
                    "description": content[:2000],  # Discord has a 2000 char limit
                    "color": color
                }
            ]
        }
        
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload
        )
        
        if response.status_code >= 400:
            print(f"Failed to send Discord message: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

def get_recently_played():
    try:
        print(f"Fetching data for username: {lastfm_username}")
        if not lastfm_api_key or not lastfm_username:
            error_msg = "ERROR: Last.fm API key or username is not set in environment variables."
            print(error_msg)
            send_discord_message(error_msg, title="Last.fm Credentials Missing", success=False)
            return None
            
        url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={lastfm_username}&api_key={lastfm_api_key}&format=json&limit=1"
        print(f"Making request to: {url}")
        
        response = requests.get(url)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            error_msg = f"API request failed with status code {response.status_code}\nResponse content: {response.text[:1000]}"
            print(error_msg)
            send_discord_message(error_msg, title="Last.fm API Error", success=False)
            return None
            
        data = response.json()
        print("API response received:")
        print(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
        
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
    except Exception as e:
        error_msg = f"Error in get_recently_played: {e}\n{traceback.format_exc()}"
        print(error_msg)
        send_discord_message(error_msg, title="Script Exception", success=False)
        return None

def update_readme(track_info):
    if not track_info:
        print("No track information available to update README.")
        return
    
    try:
        readme_path = 'README.md'
        print(f"Looking for README at: {os.path.abspath(readme_path)}")
        
        if not os.path.exists(readme_path):
            error_msg = f"ERROR: README.md file not found at {os.path.abspath(readme_path)}\nCurrent directory contents: {os.listdir('.')}"
            print(error_msg)
            send_discord_message(error_msg, title="README Not Found", success=False)
            return
            
        with open(readme_path, 'r', encoding='utf-8') as file:
            content = file.read()
            print(f"README file loaded, size: {len(content)} characters")
        
        start_marker = "<!-- YOUTUBE-MUSIC-START -->"
        end_marker = "<!-- YOUTUBE-MUSIC-END -->"
        
        print(f"Start marker present: {start_marker in content}")
        print(f"End marker present: {end_marker in content}")
        
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
            print("Replaced existing music section in README")
        else:
            print("Markers not found in README, appending music section")
            new_content = content + "\n\n" + music_section
        
        with open(readme_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
            success_msg = f"README updated successfully with '{track_info['song_name']}' by {track_info['artist']}"
            print(success_msg)
            send_discord_message(success_msg, title="README Update Success", success=True)
            
    except Exception as e:
        error_msg = f"Error updating README: {e}\n{traceback.format_exc()}"
        print(error_msg)
        send_discord_message(error_msg, title="README Update Failed", success=False)

if __name__ == "__main__":
    try:
        print("Starting YouTube Music README update script")
        send_discord_message("Starting YouTube Music README update script", title="Script Started", success=True)
        print(f"Python version: {sys.version}")
        print(f"Current working directory: {os.getcwd()}")
        
        track_info = get_recently_played()
        if track_info:
            print(f"Track info retrieved: {track_info['song_name']} by {track_info['artist']}")
            update_readme(track_info)
        else:
            error_msg = "No recently played tracks found or there was an error fetching the data."
            print(error_msg)
            send_discord_message(error_msg, title="No Track Data", success=False)
    except Exception as e:
        error_msg = f"Unexpected error in main: {e}\n{traceback.format_exc()}"
        print(error_msg)
        send_discord_message(error_msg, title="Critical Error", success=False)
