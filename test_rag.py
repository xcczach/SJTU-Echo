from backend.rag import get_hf_vectorstore, inference
from langchain_core.messages import HumanMessage
from utils.models import QwenModel

vectorstore = get_hf_vectorstore("test_output/sample_embeddings")
chat_model = QwenModel(model="Qwen/Qwen2.5-1.5B-Instruct")
messages = [HumanMessage(content="科技创新行动计划的申报要求")]
answer, _ = inference(messages, chat_model, vectorstore)
print(answer.content)
print(answer.response_metadata)
