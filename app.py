from flask import Flask, send_from_directory
from endpoints.reset import reset
from endpoints.api import api
from flask_cors import CORS
from sys import argv

app = Flask(__name__)
app.register_blueprint(reset)
app.register_blueprint(api)
CORS(app)

@app.route('/')
def index():
    return "This is our project! Love, Alex and Javid. :)"

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path + '/assets', 'favicon.ico')

if __name__ == "__main__":
    if len(argv) >= 2:
        if argv[1] == "START_SERVER":
            app.run("0.0.0.0", 9000)
        else:
            app.run("0.0.0.0")
    else:
        app.run("0.0.0.0")