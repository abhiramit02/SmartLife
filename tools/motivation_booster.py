import random
import os
import requests

# ✅ Spotify Playlists (fallbacks)
spotify_playlists = [
    "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
    "https://open.spotify.com/playlist/37i9dQZF1DWYmmr74INQlb",
    "https://open.spotify.com/playlist/37i9dQZF1DX76Wlfdnj7AP",
]

# ✅ YouTube Motivational Videos (fallbacks)
youtube_videos = [
    "https://www.youtube.com/watch?v=mgmVOuLgFB0",
    "https://www.youtube.com/watch?v=ZXsQAXx_ao0",
    "https://www.youtube.com/watch?v=wnHW6o8WMas",
]

# ✅ Nature Sounds (fallbacks)
nature_videos = [
    "https://www.youtube.com/watch?v=1ZYbU82GVz4",
    "https://www.youtube.com/watch?v=OdIJ2x3nxzQ",
    "https://www.youtube.com/watch?v=ZToicYcHIOU",
]

# ✅ Dynamic YouTube search via API
def get_youtube_video_by_query(query):
    api_key = os.getenv("YOUTUBE_API_KEY")
    print(f"🔍 Searching YouTube for: {query}")
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "key": api_key
    }

    try:
        res = requests.get(search_url, params=params)
        print("📦 Response status:", res.status_code)
        print("📨 Response JSON:", res.json())

        if res.status_code == 200:
            items = res.json().get("items", [])
            if items:
                video_id = items[0]["id"]["videoId"]
                return f"https://www.youtube.com/watch?v={video_id}"
            else:
                print("❌ No video items found in response.")
        else:
            print(f"❌ Error: Status {res.status_code}")
        return None
    except Exception as e:
        print(f"[❌ YouTube API Exception] {e}")
        return None

# ✅ Add these functions to avoid import error
def get_random_spotify_playlist():
    return random.choice(spotify_playlists)

def get_random_youtube_video():
    return random.choice(youtube_videos)

def get_random_nature_video():
    return random.choice(nature_videos)
