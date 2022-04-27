import socket
from flask import Flask
from flask import jsonify
from flask_cors import CORS
from ...link_handler import download_link_data
from ...data_handler import insert_data, retrieve_all_data, retrieve_data

HOST = '' # bind to a bunch of stuff? idk lol
PORT_WEB = 8080
queue = []

app = Flask(__name__)
# NEED THIS FOR WEBSERVER TO FLASK SERVER COMMUNICATION
CORS(app,resources={r"/*":{"http://localhost:5000/":"*","http://localhost":"*"}})

# Connects to TCP Server socket and sends the length of
# the link as 1 byte, and then sends the link over the socket.
def send_link_socket(link=None):
    if not link:
        return False
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((HOST, PORT_WEB))

            # Encode link to bytes, and get length of this as a 1-byte marker for message
            data = link.encode("utf-8")
            marker = len(data).to_bytes(1,"big")

            # Send the marker and the data over the socket
            s.send(marker)
            s.send(data)
            return True
    except Exception as e:
        print(e)
        return False

# POST Request
@app.route('/download_link/<link>')
@app.route('/download_link/')
def download_link(link=None):
    if not link:
        return {'message': 'No link given'}
    data = download_link_data(link)
    if not data:
        return {'message': 'Invalid link given'}
    title, duration, yt_link, filepath, thumbnail = data

    # Insert the data extracted into the db for future use.
    inserted = insert_data(title, duration, yt_link, filepath, thumbnail)

    obj = {'title': title, 'thumbnail': thumbnail}
    queue.append(obj)
    return jsonify(queue)

@app.route('/all_song_info/')
def all_song_info():
    data = retrieve_all_data()
    data = [{"timestamp": item[0],
            "title": item[1],
            "length": item[2],
            "link": item[3],
            "filepath": item[4],
            "thumbnail": item[5]} for item in data]
    return {'message': 'All song info successfully retrived', 'data': data}

# GET Request
@app.route('/get_queue/')
def get_queue():
    return jsonify(queue)

@app.route('/add_song_queue/<link>')
@app.route('/add_song_queue/')
def add_song_queue(link=None):
    if not link:
        return {'message': 'No link given'}
    data = retrieve_data(link)
    if not data:
        return {'message': 'Invalid link given'}
    timestamp, title, duration, yt_link, filepath, thumbnail = data

    obj = {'title': title, 'link': yt_link, 'thumbnail': thumbnail}
    queue.append(obj)
    return obj

@app.route('/play_song/<link>')
@app.route('/play_song/')
def play_song(link=None):
    if not link:
        return {'message': 'No link given'}
    
    link_sent = send_link_socket(link)
    if link_sent:
        return {'message': 'Link sent'}
    return {'message': 'Link failed to send'}
    

