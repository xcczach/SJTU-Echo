import setproctitle
from utils.models import QwenModel
from backend.rag import get_hf_vectorstore, messages_to_json, json_to_messages
from backend.rag import inference as rag_inference
from backend.tts import get_tts_model_and_config
from backend.tts import inference as tts_inference
from backend.asr import get_asr_model
from backend.asr import inference as asr_inference
from fastapi import FastAPI, Request
from ml_web_inference import StreamingResponse, Response
import uvicorn

chat_model = None
vectorstore = None
tts_model = None
tts_config = None
asr_model = None
def launch_server(chat_model_name: str, hf_vectorstore_source_dir: str, port: int):
    global chat_model, vectorstore
    setproctitle.setproctitle('SJTU-Echo-Server')

    if chat_model_name.startswith("Qwen/"):
        chat_model = QwenModel(model=chat_model_name)
    else:
        raise ValueError(f"Unknown chat model: {chat_model_name}")
    vectorstore = get_hf_vectorstore(hf_vectorstore_source_dir)

    tts_model, tts_config = get_tts_model_and_config()

    asr_model = get_asr_model()

    app = FastAPI()
    @app.post("/rag")
    async def rag(request: Request):
        messages_json = await request.json()
        messages = json_to_messages(messages_json)
        new_message = rag_inference(messages, chat_model, vectorstore)
        return messages_to_json([new_message])
    @app.post("/tts")
    async def tts(request: Request):
        data = await request.json()
        text = data["text"]
        result = tts_inference(text, tts_model, tts_config)
        return StreamingResponse(result, media_type="application/octet-stream")
    @app.post("/asr")
    async def asr(request: Request):
        data = await request.json()
        sample_rate = data["sample_rate"]
        audio_data = data["audio_data"]
        result = asr_inference(audio_data, sample_rate, asr_model)
        return Response(content=result, media_type="text/plain")

    host = "localhost"
    uvicorn.run(app, host=host, port=port, log_level="info")
