import socket
from flask import Flask
from flask import jsonify
from flask_cors import CORS
from ...link_handler import download_link_data
from ...data_handler import insert_data, retrieve_all_data, retrieve_data
import threading
import time

HOST = '' # bind to a bunch of stuff? idk lol
PORT_WEB = 8080
queue = []
queue_handling = False  # Boolean of whether or not the API is currently handling the queue
NEXT_SONG_RATIO = 0.8   # Sends next song in queue after current song is 80% done playing

app = Flask(__name__)
# NEED THIS FOR WEBSERVER TO FLASK SERVER COMMUNICATION
CORS(app,resources={r"/*":{"http://localhost:5000/":"*","http://localhost":"*"}})

# Connects to TCP Server socket and sends the length of
# the link as 1 byte, and then sends the link over the socket.
def send_link_socket(link=None, command=None):
    if not link:
        return False
    if not command:
        return False
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((HOST, PORT_WEB))

            # Encode link to bytes, and get length of this as a 1-byte marker for message
            data = link.encode("utf-8")
            marker = (len(data)+1).to_bytes(1,"big")
            cmd = command.to_bytes(1,"big")

            # Send the marker, command, and data over the socket
            s.send(marker)
            s.send(cmd)
            s.send(data)
            return True
    except Exception as e:
        print(e)
        return False

def handle_queue():
    global queue_handling
    # Send first song in queue over socket, and monitor the queue
    next_song_valid = False
    song_start_time = time.time()
    song_duration = queue[0]['duration']
    send_link_socket(queue[0]['link'], 6)

    while len(queue):
        # Send next song if next song to play is updated, and song playing is almost over
        if not next_song_valid and time.time() - song_start_time > song_duration * NEXT_SONG_RATIO:
            next_song_valid = True
            send_link_socket(queue[1]['link'], 5)

        # If song is over, update queue by removing first element and updating indices
        if time.time() - song_start_time > song_duration:
            queue = queue[1:]
            for song in queue:
                song['index'] -= 1
            
            # Update state variables for queue checking
            next_song_valid = False
            song_start_time = time.time()
            song_duration = queue[0]['duration']

    queue_handling = False
    return

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

    obj = {'title': title, 'link': yt_link, 'thumbnail': thumbnail}
    return jsonify(obj)

@app.route('/all_song_info/')
def all_song_info():
    data = retrieve_all_data()
    data = [{"timestamp": item[0],
            "title": item[1],
            "duration": item[2],
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
    global queue
    global queue_handling
    if not link:
        return {'message': 'No link given'}
    data = retrieve_data(link)
    if not data:
        return {'message': 'Invalid link given'}
    timestamp, title, duration, yt_link, filepath, thumbnail = data

    obj = {'title': title, 'duration': duration, 'link': yt_link, 'thumbnail': thumbnail, 'index': len(queue)}
    queue.append(obj)

    # If queue has length now and was not being handled, start handler
    if len(queue) and not queue_handling:
        queue_handling = True
        # Thread for maintaining queue as a running process until queue depletes
        web_thread = threading.Thread(target=handle_queue)
        web_thread.daemon = True
        web_thread.start()
        
    return obj

@app.route('/remove_song_queue/<link>/<index>')
@app.route('/remove_song_queue/<link>')
@app.route('/remove_song_queue/')
def remove_song_queue(link=None, index=None):
    global queue
    if not link:
        return {'message': 'No link given'}
    if not index:
        return {'message': 'No index given'}
    ind = int(index)

    data = retrieve_data(link)
    if not data:
        return {'message': 'Invalid link given'}
    timestamp, title, duration, yt_link, filepath, thumbnail = data

    # Remove song with matching link and index, as well as decrement correct indices in queue
    temp_queue = []
    for song in queue:
        if song['index'] != ind or song['link'] != yt_link:
            temp_queue.append(song)
    for song_ind in range(len(temp_queue)):
        temp_queue[song_ind]['index'] = song_ind
    queue = temp_queue
        
    return {'title': title, 'duration': duration, 'link': yt_link, 'thumbnail': thumbnail}
