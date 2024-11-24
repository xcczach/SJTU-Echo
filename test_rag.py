from backend.rag import get_hf_vectorstore, get_answer
from langchain_core.messages import HumanMessage
from utils.models import QwenModel
vectorstore = get_hf_vectorstore("output/sample_embeddings")
chat_model = QwenModel(model="Qwen/Qwen2.5-1.5B-Instruct")
messages = [HumanMessage(content="科技创新行动计划的申报要求")]
answer = get_answer(messages, chat_model, vectorstore)
print(answer.content)
print(answer.response_metadata["link"])