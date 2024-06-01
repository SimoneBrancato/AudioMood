import whisper
import requests
from audio_downloader import get_youtube_audio
from flask import Flask, request
import os

app = Flask(__name__)
LOGSTASH_URL = "http://logstash:9700"

def splitter(text, max_words):
    pieces = text.split()
    return (" ".join(pieces[i:i+max_words]) for i in range(0, len(pieces), max_words))

@app.route('/send', methods=['POST'])
def send():
    url = request.get_json()['user_input']
    model_size = request.get_json()['model_size']
    mp3_file = get_youtube_audio(url)
    
    print(f"OpenAI Whisper model size set to {model_size}")
    model = whisper.load_model(model_size)

    print("Audio analysis in process...")
    result = model.transcribe(mp3_file)
    
    # phrases = result["text"].split(".")

    for phrase in splitter(text = result["text"], max_words = 10):
        print("Sending to Logstash \""+phrase+"\".")
        data = { 
        'message': phrase
        }
        requests.post(LOGSTASH_URL, json=data)

    return os.path.basename(mp3_file)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)



