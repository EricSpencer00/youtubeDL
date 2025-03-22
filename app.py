import os
import re
import yt_dlp
from textblob import TextBlob

def clean_title(title):
    """Removes unnecessary characters from title"""
    return re.sub(r'[<>:"/\\|?*]', '', title)

def extract_metadata(title):
    """Uses NLP to guess the artist and song title"""
    parts = title.split("-")
    if len(parts) == 2:
        artist, song = parts[0].strip(), parts[1].strip()
    else:
        blob = TextBlob(title)
        words = blob.words
        if len(words) > 2:
            artist, song = words[0], " ".join(words[1:])
        else:
            artist, song = "Unknown", title
    return artist, song

def download_video(youtube_url, format_choice):
    """Downloads the YouTube video as MP3 or MP4"""
    
    download_path = os.path.expanduser('~/Downloads')  # Save to ~/Downloads
    
    if format_choice == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'extract_audio': True,
            'audio_format': 'mp3',
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    elif format_choice == 'mp4':
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',  # Ensures MP4 output
        }
    else:
        print("⚠️ Invalid format choice. Please enter 'mp3' or 'mp4'.")
        return

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        title = clean_title(info['title'])  # Get the video title
        filename = os.path.join(download_path, f"{title}.mp4" if format_choice == 'mp4' else f"{title}.mp3")
        
        print(f"✅ File saved as: {filename}")

if __name__ == "__main__":
    youtube_url = input("🎥 Enter YouTube URL: ")
    format_choice = input("🎵 Download as MP3 or 🎬 MP4? (mp3/mp4): ").strip().lower()
    download_video(youtube_url, format_choice)
