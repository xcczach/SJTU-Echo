import setproctitle
from utils.models import QwenModel
from backend.rag import get_hf_vectorstore, inference, messages_to_json, json_to_messages
from fastapi import FastAPI, Request
import uvicorn

chat_model = None
vectorstore = None
def launch_server(chat_model_name: str, hf_vectorstore_source_dir: str, port: int):
    global chat_model, vectorstore
    setproctitle.setproctitle('SJTU-Echo-Server')

    if chat_model_name.startswith("Qwen/"):
        chat_model = QwenModel(model=chat_model_name)
    else:
        raise ValueError(f"Unknown chat model: {chat_model_name}")
    vectorstore = get_hf_vectorstore(hf_vectorstore_source_dir)

    app = FastAPI()
    @app.post("/rag")
    async def rag(request: Request):
        messages_json = await request.json()
        messages = json_to_messages(messages_json)
        new_message = inference(messages, chat_model, vectorstore)
        return messages_to_json([new_message])

    host = "localhost"
    uvicorn.run(app, host=host, port=port, log_level="info")
