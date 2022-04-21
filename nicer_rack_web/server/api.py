from flask import Flask
from flask_cors import CORS
import link_handler
import data_handler

app = Flask(__name__)
# NEED THIS FOR WEBSERVER TO FLASK SERVER COMMUNICATION
CORS(app,resources={r"/*":{"http://localhost:3000/":"*","http://localhost":"*"}})

# POST Request
@app.route('/add_link/<link>')
@app.route('/add_link/')
def add_link(link=None):
    if not link:
        return
    title, duration, yt_link, filepath, thumbnail = link_handler.extract_link_data(link)
    data_handler.insert_data(title, duration, yt_link, filepath, thumbnail)


# GET Request
@app.route('/get_queue')
def get_queue():
    message = {'greeting': 'Hello from flask'}
    return message
