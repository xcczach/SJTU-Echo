## Usage
Install the requirements (may need to install `torch` and `torchaudio` manually):
```bash
pip install -r requirements.txt
```

Start the model server:
```bash
python main.py
```

Send a test POST request to the server:
```bash
python test_client.py
```