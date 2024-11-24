import json
from typing import Iterator

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from bs4 import BeautifulSoup
from typing import Callable
from langchain_core.language_models import BaseChatModel
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

def embedding_strategy_hypothetical_question(docs: list[Document], embeddings_model: Embeddings, result_path: str,chat_model: BaseChatModel=QwenModel("Qwen/Qwen2.5-1.5B-Instruct")):
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
    print("Embedding hypothetical questions")
    Chroma.from_documents(documents=hypothetical_questions, embedding=embeddings_model, persist_directory=result_path)

def save_vectorstore_from_huggingface(content_json_path: str, result_path: str, embedding_model_name: str, embedding_strategy: Callable[[list[Document], Embeddings, str], None]=
                                      lambda docs, embeddings_model, result_path: embedding_strategy_hypothetical_question(docs, embeddings_model, result_path)):
    """
    Create vectorstore from content_json_path (created from extract_content) with embedding_model_name; save the results result_path
    """
    if not os.path.exists(result_path):
        os.makedirs(result_path)
    with open("embedding_metadata.json", "w") as f:
        json.dump({"embedding_model_name": embedding_model_name}, f)
    loader = HTMLJSONLoader(content_json_path)
    docs = loader.load()
    embeddings_model = HuggingFaceEmbeddings(model_name=embedding_model_name, model_kwargs={"trust_remote_code": True})
    embedding_strategy(docs, embeddings_model, result_path)