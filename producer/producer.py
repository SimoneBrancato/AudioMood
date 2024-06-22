import whisper
import requests
from audio_downloader import get_youtube_audio
from flask import Flask, request
import os

app = Flask(__name__)
LOGSTASH_URL = "http://logstash:9700"

# Split large text into chunks
def splitter(text, max_words):
    pieces = text.split()
    return (" ".join(pieces[i:i+max_words]) for i in range(0, len(pieces), max_words))

@app.route('/send', methods=['POST'])
def send():
    # Retrieve URL, Whisper Model Size and download audio file
    url = request.get_json()['user_input']
    model_size = request.get_json()['model_size']
    mp3_file = get_youtube_audio(url)
    
    # Load OpenAI Whisper Model
    model = whisper.load_model(model_size)

    # Transcribe audio to text
    result = model.transcribe(mp3_file)
    text = result["text"]

    # Send full text JSON to Logstash to do text summarization
    data = {
        'message': text,
        'isFullText': 1
    }
    requests.post(LOGSTASH_URL, json=data)
    
    # Split full text into chunks and send each of them to Logstash
    phrase_id = 0
    for phrase in splitter(text = result["text"], max_words = 15):

        data = { 
            'id': phrase_id,
            'message': phrase,
            'isFullText': 0
        }

        phrase_id += 1
        requests.post(LOGSTASH_URL, json=data)

    return os.path.basename(mp3_file)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)



