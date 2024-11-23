from flask import Flask, request, jsonify
from flask_cors import CORS
from time import sleep

app = Flask(__name__)
CORS(app)

@app.route('/send-message', methods=['POST'])
def send_message():
    prompt = request.json
    sessionID = prompt.get('sessionID')
    content = prompt.get('content')

    sleep(2)
    print(f"Received message - Session ID: {sessionID}, Content: {content}")

    return jsonify({"status": "success", "message": "Message received successfully."})

if __name__ == '__main__':
    app.run(debug=True)
