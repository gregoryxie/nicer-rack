from flask import Flask
from flask_cors import CORS
from ...link_handler import extract_link_data
from ...data_handler import insert_data, retrieve_all_data

queue = []

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
    obj = {'title': title, 'thumbnail': thumbnail}
    queue.append(obj)
    return jsonify(queue)

@app.route('/all_song_info/')
def all_song_info():
    return retrieve_all_data()

# GET Request
@app.route('/get_queue/')
def get_queue():
    return jsonify(queue)

@app.route('/add_song_queue/<link>')
@app.route('/add_song_queue/')
def add_song_queue(link=None):
    if not link:
        return {'message': 'No link given'}
    data = extract_link_data(link)
    if not data:
        return {'message': 'Invalid link given'}
    title, duration, yt_link, filepath, thumbnail = data

    obj = {'title': title, 'thumbnail': thumbnail}
    queue.append(obj)
    return obj


