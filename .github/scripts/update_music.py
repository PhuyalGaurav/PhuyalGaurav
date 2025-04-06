import os
import requests
import re
import traceback

lastfm_api_key = os.environ.get("LASTFM_API_KEY")
lastfm_username = os.environ.get("LASTFM_USERNAME", "gauravphuyal")

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def send_discord_message(content, title=None, success=True):
    """Send a message to Discord webhook"""
    try:
        if not DISCORD_WEBHOOK_URL:
            return
            
        color = 0x00FF00 if success else 0xFF0000
        payload = {
            "embeds": [
                {
                    "title": title or ("Music Update Success" if success else "Music Update Error"),
                    "description": content[:2000],
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
        if not lastfm_api_key or not lastfm_username:
            error_msg = "ERROR: Last.fm API key or username is not set in environment variables."
            send_discord_message(error_msg, title="Last.fm Credentials Missing", success=False)
            return None
            
        url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={lastfm_username}&api_key={lastfm_api_key}&format=json&limit=1"
        
        response = requests.get(url)
        
        if response.status_code != 200:
            error_msg = f"API request failed with status code {response.status_code}\nResponse content: {response.text[:1000]}"
            send_discord_message(error_msg, title="Last.fm API Error", success=False)
            return None
            
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
    except Exception as e:
        error_msg = f"Error in get_recently_played: {e}\n{traceback.format_exc()}"
        send_discord_message(error_msg, title="Script Exception", success=False)
        return None

def update_readme(track_info):
    if not track_info:
        return
    
    try:
        readme_path = 'README.md'
        
        if not os.path.exists(readme_path):
            error_msg = f"ERROR: README.md file not found at {os.path.abspath(readme_path)}\nCurrent directory contents: {os.listdir('.')}"
            send_discord_message(error_msg, title="README Not Found", success=False)
            return
            
        with open(readme_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        start_marker = "<!-- YOUTUBE-MUSIC-START -->"
        end_marker = "<!-- YOUTUBE-MUSIC-END -->"
        
        music_section = f"{start_marker}\n"
        music_section += "<div align='center'>\n\n"
        
        status_emoji = "🎧" if track_info['status'] == "Now playing" else "🎵"
        music_section += f"## {status_emoji} {track_info['status']} on YouTube Music\n\n"
        
        if track_info['image_url']:
            music_section += "<kbd>\n\n"
            music_section += f"[![{track_info['song_name']}]({track_info['image_url']})]({track_info['image_url']})\n\n"
            music_section += "</kbd>\n\n"
        
        search_query = f"{track_info['artist']} {track_info['song_name']}"
        music_section += f"### [{track_info['song_name']}](https://www.youtube.com/results?search_query={requests.utils.quote(search_query)})\n\n"
        
        music_section += f"**🎤 Artist:** {track_info['artist']}\n\n"
        
        if track_info['album']:
            music_section += f"**💿 Album:** {track_info['album']}\n\n"
        
        from datetime import datetime
        import pytz
        
        try:
            nepal_timezone = pytz.timezone('Asia/Kathmandu')
            current_time_utc = datetime.now(pytz.UTC)
            current_time_nepal = current_time_utc.astimezone(nepal_timezone)
            nepal_time_str = current_time_nepal.strftime("%Y-%m-%d %H:%M:%S")
            music_section += f"<sub>Last updated: {nepal_time_str} (Nepal Time)</sub>\n\n"
        except ImportError:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            music_section += f"<sub>Last updated: {current_time}</sub>\n\n"
        
        music_section += "</div>\n\n"
        music_section += end_marker
        
        if start_marker in content and end_marker in content:
            pattern = re.compile(f"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL)
            new_content = pattern.sub(music_section, content)
        else:
            new_content = content + "\n\n" + music_section
        
        with open(readme_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
            success_msg = f"README updated successfully with '{track_info['song_name']}' by {track_info['artist']}"
            send_discord_message(success_msg, title="README Update Success", success=True)
            
    except Exception as e:
        error_msg = f"Error updating README: {e}\n{traceback.format_exc()}"
        send_discord_message(error_msg, title="README Update Failed", success=False)

if __name__ == "__main__":
    try:
        send_discord_message("Starting YouTube Music README update script", title="Script Started", success=True)
        
        track_info = get_recently_played()
        if track_info:
            update_readme(track_info)
        else:
            error_msg = "No recently played tracks found or there was an error fetching the data."
            send_discord_message(error_msg, title="No Track Data", success=False)
    except Exception as e:
        error_msg = f"Unexpected error in main: {e}\n{traceback.format_exc()}"
        send_discord_message(error_msg, title="Critical Error", success=False)
