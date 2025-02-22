import json
from typing import Iterator, Literal

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from bs4 import BeautifulSoup
from typing import Literal
from utils.models import QwenModel
import os
from tqdm.auto import tqdm


def _get_content_by_key_recursive(data:dict, key:str):
    for k, v in data.items():
        if k == key:
            return v
        elif isinstance(v, dict):
            return _get_content_by_key_recursive(v, key)
    print(f"_get_content_by_key_recursive: Key {key} not found in data")
    return ""
    
def _traverse_dict(data:dict, exclude_key:str):
    result = {}
    for k, v in data.items():
        if k == exclude_key:
            continue
        if isinstance(v, dict):
            result.update(_traverse_dict(v, exclude_key))
        else:
            result[k] = v
    return result


class HTMLJSONLoader(BaseLoader):
    def __init__(self, file_path: str, content_key="body"):
        self.file_path = file_path
        self.content_key = content_key
    def lazy_load(self) -> Iterator[Document]:
        with open(self.file_path) as f:
            data = json.load(f)
            for item in data:
                page_content = _get_content_by_key_recursive(item, self.content_key)
                metadata = _traverse_dict(item, self.content_key)
                yield Document(page_content=page_content, metadata=metadata)

def _cache_documents(docs: list[Document], cache_dir: str):
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    # cache all docs in one jsonl
    with open(f"{cache_dir}/docs.jsonl", "w") as f:
        for doc in docs:
            f.write(json.dumps({
                "page_content": doc.page_content,
                "metadata": doc.metadata
            }) + "\n")

def _load_cached_documents(cache_dir: str) -> list[Document]:
    """
    Load cached documents from cache_dir
    return [] if cache file does not exist
    """
    cache_file = f"{cache_dir}/docs.jsonl"
    if not os.path.exists(cache_file):
        return []
    docs = []
    with open(f"{cache_dir}/docs.jsonl") as f:
        for line in f:
            doc_data = json.loads(line)
            doc = Document(page_content=doc_data["page_content"], metadata=doc_data["metadata"])
            docs.append(doc)
    return docs

def _record_current_embedded_doc(doc_index: int, result_path: str):

    with open(f"{result_path}/embedding_metadata.json", "r") as f:
        metadata = json.load(f)
    metadata["current_embedded_doc"] = doc_index
    with open(f"{result_path}/embedding_metadata.json", "w") as f:
        json.dump(metadata, f)

def _load_current_embedded_doc_index(result_path: str) -> int:
    with open(f"{result_path}/embedding_metadata.json") as f:
        metadata = json.load(f)
        return metadata.get("current_embedded_doc", 0)

def _batch_add_documents(vectorstore: Chroma, docs: list[Document], result_path: str, batch_size: int=16):
    start_index = _load_current_embedded_doc_index(result_path)
    progress = tqdm(total=len(docs)-start_index, desc="Adding documents to vectorstore")
    for i in range(start_index, len(docs), batch_size):
        vectorstore.add_documents(docs[i:i+batch_size])
        _record_current_embedded_doc(i+batch_size, result_path)
        progress.update(batch_size)


def _embedding_strategy_raw(docs: list[Document], embeddings_model: Embeddings, result_path: str, batch_size: int=16):
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=100, add_start_index=True
        )
    all_splits = text_splitter.split_documents(docs)
    vectorstore = Chroma(persist_directory=result_path, embedding_function=embeddings_model)
    _batch_add_documents(vectorstore, all_splits, result_path, batch_size)
    
def _embedding_strategy_hypothetical_question(docs: list[Document], embeddings_model: Embeddings, result_path: str, batch_size: int=16,chat_model_name: str="Qwen/Qwen2.5-1.5B-Instruct"):
    def generate_hypothetical_question(doc: Document, llm):
        from langchain_core.prompts import PromptTemplate
        template = PromptTemplate(
            input_variables=["context"],
            template="基于以下内容生成一个相关但未明确提及的假设性问题：\n\n{context}"
        )
        prompt = template.format(context=doc.page_content)
        question = llm.invoke(prompt).content
        return question

    def clean_html_content(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    hypothetical_questions = _load_cached_documents(result_path)
    if not hypothetical_questions:
        if not chat_model_name.startswith("Qwen"):
            raise ValueError(f"Unsupported chat model: {chat_model_name}")
        chat_model = QwenModel(model=chat_model_name)
        for doc in docs:
            doc.page_content = clean_html_content(doc.page_content)
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=100, add_start_index=True
        )
        all_splits = text_splitter.split_documents(docs)
        hypothetical_questions = []
        for doc in tqdm(all_splits, desc="Generating hypothetical questions"):
            hypothetical_question = generate_hypothetical_question(doc, chat_model)
            hypothetical_question_doc = Document(page_content=hypothetical_question, metadata={"original_doc": doc.page_content, **doc.metadata})
            hypothetical_questions.append(hypothetical_question_doc)
        _cache_documents(hypothetical_questions, result_path)
        print("Cached hypothetical questions")
        print("IMPORTANT: If you meet GPU memory issues, you can start this process again to directly load from cache")
    else:
        print("Hypothetical questions loaded from cache")
    print("Embedding hypothetical questions")
    vectorstore = Chroma(persist_directory=result_path, embedding_function=embeddings_model)
    _batch_add_documents(vectorstore, hypothetical_questions, result_path, batch_size)

def _embedding_strategy_hypothetical_question_with_raw(docs: list[Document], embeddings_model: Embeddings, result_path: str, batch_size: int=16,chat_model_name: str="Qwen/Qwen2.5-1.5B-Instruct"):
    def generate_hypothetical_question(doc: Document, llm):
        from langchain_core.prompts import PromptTemplate
        template = PromptTemplate(
            input_variables=["context"],
            template="基于以下内容生成一个相关但未明确提及的假设性问题：\n\n{context}"
        )
        prompt = template.format(context=doc.page_content)
        question = llm.invoke(prompt).content
        return question

    def clean_html_content(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    hypothetical_questions = _load_cached_documents(result_path)
    if not hypothetical_questions:
        if not chat_model_name.startswith("Qwen"):
            raise ValueError(f"Unsupported chat model: {chat_model_name}")
        chat_model = QwenModel(model=chat_model_name)
        for doc in docs:
            doc.page_content = clean_html_content(doc.page_content)
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=100, add_start_index=True
        )
        all_splits = text_splitter.split_documents(docs)
        hypothetical_questions_doc = []
        for doc in tqdm(all_splits, desc="Generating hypothetical questions"):
            hypothetical_question = generate_hypothetical_question(doc, chat_model)
            page_content = "Hypothetical question: " + hypothetical_question + "\n\nContext: " + doc.page_content
            hypothetical_question_doc = Document(page_content=page_content, metadata=doc.metadata)
            hypothetical_questions.append(hypothetical_question_doc)
        _cache_documents(hypothetical_questions_doc, result_path)
        print("Cached hypothetical question docs")
        print("IMPORTANT: If you meet GPU memory issues, you can start this process again to directly load from cache")
    else:
        print("Hypothetical question docs loaded from cache")
    print("Embedding hypothetical question docs")
    vectorstore = Chroma(persist_directory=result_path, embedding_function=embeddings_model)
    _batch_add_documents(vectorstore, hypothetical_questions, result_path, batch_size)

EmbeddingStrategy = Literal["hypothetical_question", "raw", "hypothetical_question_with_raw"]
def save_vectorstore_from_huggingface(content_json_path: str, result_path: str, embedding_model_name: str, embedding_strategy: EmbeddingStrategy="hypothetical_question", batch_size: int=16):
    """
    Create vectorstore from content_json_path (created from extract_content) with embedding_model_name; save the results result_path
    """
    if not os.path.exists(result_path):
        os.makedirs(result_path)
    embedding_metadata_json = f"{result_path}/embedding_metadata.json"
    if not os.path.exists(embedding_metadata_json):
        with open(embedding_metadata_json, "w") as f:
            json.dump({"embedding_model_name": embedding_model_name}, f)
    loader = HTMLJSONLoader(content_json_path)
    docs = loader.load()
    embeddings_model = HuggingFaceEmbeddings(model_name=embedding_model_name, model_kwargs={"trust_remote_code": True})

    if embedding_strategy == "hypothetical_question":
        embedding_func = _embedding_strategy_hypothetical_question
    elif embedding_strategy == "raw":
        embedding_func = _embedding_strategy_raw
    elif embedding_strategy == "hypothetical_question_with_raw":
        embedding_func = _embedding_strategy_hypothetical_question_with_raw
    else:
        raise ValueError(f"Unknown embedding strategy: {embedding_strategy}")
    embedding_func(docs, embeddings_model, result_path, batch_size)