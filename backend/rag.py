from langchain_chroma import Chroma
import json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.vectorstores import VectorStore
from langchain import hub
from typing import Literal

def get_hf_vectorstore(source_dir: str):
    with open(f"{source_dir}/embedding_metadata.json", "r") as f:
        embedding_model_name = json.load(f)["embedding_model_name"]
    embeddings_model = HuggingFaceEmbeddings(model_name=embedding_model_name, model_kwargs={"trust_remote_code": True})
    vectorstore = Chroma(embedding_function=embeddings_model, persist_directory=source_dir)
    return vectorstore

_strategy_hypothetical_question_prompt = hub.pull("rlm/rag-prompt")
def _get_answer_strategy_hypothetical_question(messages: list[BaseMessage], chat_model: BaseChatModel, vectorstore: VectorStore):
    def generate_hypothetical_answer(question: str, chat_model) -> str:
        prompt_text = f"根据以下问题生成一个简洁的假设性回答，以便用于相似性检索优化：\n\n问题：{question}\n\n假设性回答："
        input_messages = [HumanMessage(content=prompt_text)]
        response = chat_model.invoke(input=input_messages).content
        return response.strip()
    question = messages[-1].content
    embeddings_model = vectorstore.embeddings
    hypothetical_answer = generate_hypothetical_answer(question, chat_model)
    hypothetical_embedding = embeddings_model.embed_query(hypothetical_answer)
    retrieved_docs = vectorstore.similarity_search_by_vector(hypothetical_embedding, k=6)
    combined_context = "\n\n".join([doc.metadata["original_doc"] for doc in retrieved_docs])
    input_messages = _strategy_hypothetical_question_prompt.invoke(
        {
            "context": combined_context, 
            "question": question
        }
    ).to_messages()
    new_messages = messages + input_messages
    # return AIMessage(content=chat_model.invoke(input=new_messages).content, response_metadata={"links": retrieved_docs[0].metadata.get("url", "")})
    links = [retrieved_doc.metadata.get("url", "") for retrieved_doc in retrieved_docs]
    links = [link for link in links if link]
    return AIMessage(content=chat_model.invoke(input=new_messages).content, response_metadata={"links": links})


def inference(messages: list[BaseMessage], chat_model: BaseChatModel, vectorstore: VectorStore, strategy: Literal["hypothetical_question"]="hypothetical_question"):
    if strategy == "hypothetical_question":
        return _get_answer_strategy_hypothetical_question(messages, chat_model, vectorstore)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    
def messages_to_json(messages: list[BaseMessage]):
    result_list = []
    for message in messages:
        result_list.append({
            "type": message.type,
            "content": message.content,
            "response_metadata": message.response_metadata
        })
    return {"messages": result_list}

def json_to_messages(json_data: dict):
    messages = []
    for message_data in json_data["messages"]:
        if message_data["type"] == "human":
            messages.append(HumanMessage(content=message_data["content"], response_metadata=message_data["response_metadata"]))
        elif message_data["type"] == "ai":
            messages.append(AIMessage(content=message_data["content"], response_metadata=message_data["response_metadata"]))
        else:
            raise ValueError(f"Unknown message type: {message_data['type']}")
    return messages