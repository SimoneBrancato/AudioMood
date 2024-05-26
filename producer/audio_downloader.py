import os
from pytube import YouTube
from pydub import AudioSegment

def get_youtube_audio(url, output_path='audio'):
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Download audio from YT
    yt = YouTube(url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_file = audio_stream.download(output_path)

    # Convert the downloaded file to MP3
    base, ext = os.path.splitext(audio_file)
    mp3_file = f"{base}.mp3"
    audio = AudioSegment.from_file(audio_file)
    audio.export(mp3_file, format="mp3")

    # Remove the original downloaded file
    os.remove(audio_file)

    print(f"Downloaded and converted to MP3: {mp3_file}")
    return mp3_file