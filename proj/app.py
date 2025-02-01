from flask import Flask, request
app = Flask(__name__)
@app.route('/hello', methods=['GET'])
def hello():
    return 'Hello World'

