# SJTU-Echo Webpage Frontend

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Environment Setup
```sh
winget install Schniz.fnm
fnm env --use-on-cd | Out-String | Invoke-Expression
fnm use --install-if-missing 22
```

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```

## Backend API
Here is a simple Flask API that you can use to test the frontend-backend communication. You can run this API on your local machine
```sh
npm install axios
```

```javascript
import axios from 'axios';

const API_URL = 'http://localhost:5000/send-message';

async function sendPrompt() {
    try {
        const response = await axios.post(apiUrl, {
          sessionID: sessionID,
          content: message.value,
        });
        if (response.status === 200) {
          const newMessage = { from: "bot", content: response.data.message, sessionID: sessionID};
          ...
        }
    } catch (error) {
    console.error(error);
    }
};
```

In the backend, you can use the following Flask API to receive the message and send a response.
```sh
pip install flask flask-cors
```

```python
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

    sleep(2) # Simulate a delay in processing the message
    print(f"Received message - Session ID: {sessionID}, Content: {content}")

    return jsonify({"status": "success", "message": "Message received successfully."})

if __name__ == '__main__':
    app.run(debug=True)
```
Then you can run the Flask API using the following command
```sh
python app.py
```
And then you can test the frontend-backend communication by sending a message from the frontend to the backend API.
