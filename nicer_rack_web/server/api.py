from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
# NEED THIS FOR WEBSERVER TO FLASK SERVER COMMUNICATION
CORS(app,resources={r"/*":{"http://localhost:3000":"*","http://localhost":"*"}})

# POST Request
@app.route('/submit_link')
def add_link():
    pass

# GET Request
@app.route('/get_queue')
def get_queue():
    message = {'greeting': 'Hello from flask'}
    return message
