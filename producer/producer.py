import whisper
import requests
from split_string import split_string
from audio_downloader import get_youtube_audio
from flask import Flask, request

app = Flask(__name__)
LOGSTASH_URL = "http://logstash:9700"

@app.route('/send', methods=['POST'])
def send():
    url = request.get_json()['user_input']
    mp3_file = get_youtube_audio(url)

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

    return "Data received and processed successfully."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)



