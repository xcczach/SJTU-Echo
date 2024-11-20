import requests
import soundfile as sf
import io

url = "http://localhost:9234/asr"
audio_data, sample_rate = sf.read("ref_audio.mp3")
data = {"sample_rate": sample_rate, "audio_data": audio_data.tolist()}

response = requests.post(url, json=data, stream=True)

if response.status_code == 200:
    print(response.text)
else:
    print(f"Bad request：{response.status_code}")
