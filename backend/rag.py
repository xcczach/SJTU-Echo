from langchain_chroma import Chroma
import json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.vectorstores import VectorStore
from langchain import hub
from typing import Literal
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

def get_hf_vectorstore(source_dir: str):
    with open(f"{source_dir}/embedding_metadata.json", "r") as f:
        embedding_model_name = json.load(f)["embedding_model_name"]
    embeddings_model = HuggingFaceEmbeddings(model_name=embedding_model_name, model_kwargs={"trust_remote_code": True})
    vectorstore = Chroma(embedding_function=embeddings_model, persist_directory=source_dir)
    return vectorstore

_rag_prompt = hub.pull("rlm/rag-prompt")

_generate_hypo_answer_prompt = ChatPromptTemplate.from_template("根据以下问题生成一个简洁的假设性回答，以便用于相似性检索优化：\n\n问题：{question}\n\n假设性回答：")
_str_output_parser = StrOutputParser()
def _create_hypo_answer_chain(chat_model: BaseChatModel):
    return _generate_hypo_answer_prompt | chat_model | _str_output_parser | (lambda x: x.strip())
def _retrieve_links_from_docs(docs: list[Document]):
    links = [retrieved_doc.metadata.get("url", "") for retrieved_doc in docs]
    return [link for link in links if link]
def _get_contexts_hypo_ques(docs: list[Document]):
    return [doc.metadata["original_doc"] for doc in docs]
def _get_question(messages: list[BaseMessage]):
    return messages[-1].content
def _enhance_latest_message(messages: list[BaseMessage], context: str):
    new_message = _rag_prompt.invoke(
        {
            "context": context, 
            "question": _get_question(messages)
        }
    ).to_messages()[-1]
    messages[-1] = new_message
def _rag_strategy_hypothetical_question(messages: list[BaseMessage], chat_model: BaseChatModel, vectorstore: VectorStore):
    question = _get_question(messages)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
    chain = _create_hypo_answer_chain(chat_model) | retriever
    retrieved_docs = chain.invoke({"question": question})

    contexts = _get_contexts_hypo_ques(retrieved_docs)
    combined_context = "\n\n".join(contexts)
    _enhance_latest_message(messages, combined_context)
    links = _retrieve_links_from_docs(retrieved_docs)
    return AIMessage(content=chat_model.invoke(input=messages).content, response_metadata={"links": links}), contexts

def _get_contexts_raw(docs: list[Document]):
    return [doc.page_content for doc in docs]
def _rag_strategy_raw(messages: list[BaseMessage], chat_model: BaseChatModel, vectorstore: VectorStore):
    question = _get_question(messages)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
    retrieved_docs = retriever.invoke(question)

    contexts = _get_contexts_raw(retrieved_docs)
    combined_context = "\n\n".join(contexts)
    _enhance_latest_message(messages, combined_context)
    links = _retrieve_links_from_docs(retrieved_docs)
    return AIMessage(content=chat_model.invoke(input=messages).content, response_metadata={"links": links}), contexts

def _rag_strategy_hypothetical_question_with_raw(messages: list[BaseMessage], chat_model: BaseChatModel, vectorstore: VectorStore):
    question = _get_question(messages)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
    chain = _create_hypo_answer_chain(chat_model) | retriever
    retrieved_docs = chain.invoke({"question": question})

    contexts = _get_contexts_raw(retrieved_docs)
    combined_context = "\n\n".join(contexts)
    _enhance_latest_message(messages, combined_context)
    links = _retrieve_links_from_docs(retrieved_docs)
    return AIMessage(content=chat_model.invoke(input=messages).content, response_metadata={"links": links}), contexts

RAGStrategy = Literal["hypothetical_question", "raw", "hypothetical_question_with_raw"]

def inference(messages: list[BaseMessage], chat_model: BaseChatModel, vectorstore: VectorStore, 
              strategy: RAGStrategy="hypothetical_question"):
    """
    returns (new_message, list[context])
    """
    if strategy == "hypothetical_question":
        return _rag_strategy_hypothetical_question(messages, chat_model, vectorstore)
    elif strategy == "raw":
        return _rag_strategy_raw(messages, chat_model, vectorstore)
    elif strategy == "hypothetical_question_with_raw":
        return _rag_strategy_hypothetical_question_with_raw(messages, chat_model, vectorstore)
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