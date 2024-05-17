import whisper
import requests
import re
from audio_downloader import get_youtube_audio

def split_string(s, max_words):
    
    parts = re.split(r'[,.]', s)
    parts = [part.strip() for part in parts if part.strip()]
    
    result = []
    current_part = []
    current_word_count = 0

    for part in parts:
        words = part.split()
        for word in words:
            if current_word_count < max_words:
                current_part.append(word)
                current_word_count += 1
            else:
                result.append(" ".join(current_part))
                current_part = [word]
                current_word_count = 1

        if current_part:
            result.append(" ".join(current_part))
            current_part = []
            current_word_count = 0
    
    return result


LOGSTASH_URL = "http://logstash:9700"
mp3_file = get_youtube_audio('https://www.youtube.com/watch?v=L6sm1_mF7E8&t=57s')

print("Audio analysis in process...")
model = whisper.load_model("tiny")
result = model.transcribe(mp3_file)

phrases = split_string(result["text"], max_words=20)

for phrase in phrases:
    print("Sending to Logstash \""+phrase+"\".")
    data = { 
    'message': phrase
    }
    response = requests.post(LOGSTASH_URL, json=data)




