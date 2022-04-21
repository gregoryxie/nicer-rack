from flask import Flask
from flask import request
from flask_cors import CORS
from flask import jsonify
from ...link_handler import extract_link_data
from ...data_handler import insert_data

app = Flask(__name__)
# NEED THIS FOR WEBSERVER TO FLASK SERVER COMMUNICATION
CORS(app,resources={r"/*":{"http://localhost:5000/":"*","http://localhost":"*"}})

# POST Request
@app.route('/add_link/<link>')
@app.route('/add_link/')
def add_link(link=None):
    if not link:
        return {'message': 'No link given'}
    data = extract_link_data(link)
    if not data:
        return {'message': 'Invalid link given'}
    title, duration, yt_link, filepath, thumbnail = data
    insert_data(title, duration, yt_link, filepath, thumbnail)
    return {'message': 'Link given, downloaded, and saved in db',
    'title': title, 'duration': duration, 'yt_link': yt_link, 'thumbnail': thumbnail}


# GET Request
@app.route('/get_queue')
def get_queue():
    message = {'greeting': 'Hello from flask'}
    return message
