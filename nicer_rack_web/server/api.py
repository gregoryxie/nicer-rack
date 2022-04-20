from flask import Flask

app = Flask(__name__)

# POST Request
@app.route('/submit_link')
def add_link():
    pass

# GET Request
@app.route('/get_queue')
def get_queue():
    return {'text': "Works"}
