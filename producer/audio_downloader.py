import os
from pytubefix import YouTube
from pytubefix.cli import on_progress
import os

def get_youtube_audio(url, output_path='audio'):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    print("Downloading from YouTube")

    # Download audio from YT
    yt = YouTube(url, on_progress_callback = on_progress)
    ys = yt.streams.get_audio_only()
    mp3_file = ys.download(mp3=True)

    print(f"Downloaded and converted to MP3: {mp3_file}")
    return mp3_file