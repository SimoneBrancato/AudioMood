import requests
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    user_input = request.form['user_input']
    response = requests.post('http://producer:5001/send', json={'user_input': user_input}) 
    return response.text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)