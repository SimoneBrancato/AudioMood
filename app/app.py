from time import sleep
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analysis', methods=['POST'])
def submit():

    user_input = request.form['user_input']
    model_size = request.form['model_size']
    
    data = {
        'user_input': user_input,
        'model_size': model_size
    }

    response = requests.post('http://producer:5001/send', json=data) 

    sleep(30)
    
    return render_template('analysis.html', file_name=response.text, model_size=model_size)

""" @app.route('/analysis_reload', methods=['POST'])
def reload():
    return render_template('analysis.html')

 """
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)