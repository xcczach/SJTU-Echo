import json
from typing import Iterator

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

def _get_content_by_key_recursive(data:dict, key:str):
    for k, v in data.items():
        if k == key:
            return v
        elif isinstance(v, dict):
            return _get_content_by_key_recursive(v, key)
    raise ValueError(f"Key {key} not found in data")
    
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

from transformers import AutoModelForCausalLM, AutoTokenizer

# model_name = "Qwen/Qwen2.5-1.5B-Instruct"

# model = AutoModelForCausalLM.from_pretrained(
#     model_name,
#     torch_dtype="auto",
#     device_map="auto"
# )
# tokenizer = AutoTokenizer.from_pretrained(model_name)

from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel, SimpleChatModel
from langchain_core.messages import AIMessageChunk, BaseMessage, HumanMessage, convert_to_openai_messages
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.runnables import run_in_executor

class QwenModel(BaseChatModel):
    def __init__(self):
        super().__init__()
        model_name = "Qwen/Qwen2.5-1.5B-Instruct"
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def _generate(self, messages: List[BaseMessage], stop: List[str] | None = None, run_manager: CallbackManagerForLLMRun | None = None, **kwargs: Any) -> ChatResult:
        oai_messages = convert_to_openai_messages(messages)
        text = self.tokenizer.apply_chat_template(
            oai_messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=512
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
if __name__ == "__main__":
    loader = HTMLJSONLoader("data/sample_contents.json")
    # for doc in loader.lazy_load():
    #     print(doc.page_content)
    #     print(doc.metadata)
    #     print("===")
    docs = loader.load()

    from langchain_text_splitters import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, add_start_index=True
    )
    all_splits = text_splitter.split_documents(docs)

    from langchain_huggingface import HuggingFaceEmbeddings
    # If applicable use Alibaba-NLP/gte-Qwen2-7B-instruct
    embeddings_model = HuggingFaceEmbeddings(model_name="Alibaba-NLP/gte-Qwen2-1.5B-instruct", model_kwargs={"trust_remote_code": True})
    
    from langchain_chroma import Chroma
    vectorstore = Chroma.from_documents(documents=all_splits, embedding=embeddings_model, persist_directory="data/chroma")
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})
    retrieved_docs = retriever.invoke("医工交叉研究基金的申报要求是什么")
    # print(retrieved_docs[0].page_content)

    from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
    # If applicable use Qwen/Qwen2.5-7B-Instruct
    llm = HuggingFaceEndpoint(
        repo_id="Qwen/Qwen2.5-1.5B-Instruct",
        task="text-generation",
    )