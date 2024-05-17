import whisper
import requests

LOGSTASH_URL = "http://logstash:9700"

print("Audio analysis in process...")
model = whisper.load_model("medium")
result = model.transcribe("audio.mp3")
print(result["text"])


phrases = result["text"].split(".")

for phrase in phrases:
    print("Sending to Logstash \""+phrase+"\".")
    data = { 
    'message': phrase
    }
    response = requests.post(LOGSTASH_URL, json=data)