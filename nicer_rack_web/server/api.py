from flask import Flask
from flask_cors import CORS
from ...link_handler import extract_link_data
from ...data_handler import insert_data

app = Flask(__name__)
# NEED THIS FOR WEBSERVER TO FLASK SERVER COMMUNICATION
CORS(app,resources={r"/*":{"http://localhost:3000/":"*","http://localhost":"*"}})

# POST Request
@app.route('/add_link/<link>')
@app.route('/add_link/')
def add_link(link=None):
    return {'text': link}
    if not link:
        return {'message': 'No link given'}
    title, duration, yt_link, filepath, thumbnail = extract_link_data(link)
    insert_data(title, duration, yt_link, filepath, thumbnail)
    return {'message': 'Link given'}


# GET Request
@app.route('/get_queue')
def get_queue():
    message = {'greeting': 'Hello from flask'}
    return message
