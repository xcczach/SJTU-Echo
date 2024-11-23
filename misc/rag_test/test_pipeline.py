import json
from bs4 import BeautifulSoup
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
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, convert_to_openai_messages
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.runnables import run_in_executor

class QwenModel(BaseChatModel):
    model: str
    def __init__(self, model: str):
        super().__init__(model=model)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model,
            torch_dtype="auto",
            device_map="auto"
        )
        self._tokenizer = AutoTokenizer.from_pretrained(self.model)

    def _generate(self, messages: List[BaseMessage], stop: List[str] | None = None, run_manager: CallbackManagerForLLMRun | None = None, **kwargs: Any) -> ChatResult:
        oai_messages = convert_to_openai_messages(messages)
        text = self._tokenizer.apply_chat_template(
            oai_messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self._tokenizer([text], return_tensors="pt").to(self._model.device)
        generated_ids = self._model.generate(
            **model_inputs,
            max_new_tokens=512
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response_text = self._tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        response_message = AIMessage(
            content=response_text
        )
        response_generation = ChatGeneration(message=response_message)
        return ChatResult(generations=[response_generation])
    
    @property
    def _llm_type(self) -> str:
        return "qwen"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model": self.model}

# 假设性问题生成函数
def generate_hypothetical_question(doc: Document, llm):
    from langchain_core.prompts import PromptTemplate
    template = PromptTemplate(
        input_variables=["context"],
        template="基于以下内容生成一个相关但未明确提及的假设性问题：\n\n{context}"
    )
    prompt = template.format(context=doc.page_content)
    question = llm.invoke(prompt).content  # 使用LLM生成假设性问题
    return question

# 为question生成假设性回答
def generate_hypothetical_answer(question: str, chat_model) -> str:
    prompt_text = f"根据以下问题生成一个简洁的假设性回答，以便用于相似性检索优化：\n\n问题：{question}\n\n假设性回答："
    input_messages = [HumanMessage(content=prompt_text)]
    response = chat_model.invoke(input=input_messages).content
    return response.strip()

def clean_html_content(html: str) -> str:
    # 使用 BeautifulSoup 解析 HTML 并提取纯文本
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

if __name__ == "__main__":
    question = input("Enter your question (enter nothing for sample question): ")
    if not question:
        question = "医工交叉研究基金的申报要求是什么"
    print("Question entered: ", question)
    loader = HTMLJSONLoader("data/sample_contents.json")
    # for doc in loader.lazy_load():
    #     print(doc.page_content)
    #     print(doc.metadata)
    #     print("===")
    docs = loader.load()
    # 清理加载的文档
    for doc in docs:
        doc.page_content = clean_html_content(doc.page_content)

    from langchain_text_splitters import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, add_start_index=True
    )
    all_splits = text_splitter.split_documents(docs)

    from langchain_huggingface import HuggingFaceEmbeddings
    # If applicable use Alibaba-NLP/gte-Qwen2-7B-instruct
    embeddings_model = HuggingFaceEmbeddings(model_name="Alibaba-NLP/gte-Qwen2-1.5B-instruct", model_kwargs={"trust_remote_code": True})
    
    # If applicable use Qwen/Qwen2.5-7B-Instruct
    chat_model = QwenModel(model="Qwen/Qwen2.5-1.5B-Instruct")

    hypothetical_questions = []
    for doc in all_splits:  # 迭代所有文档块
        hypothetical_question = generate_hypothetical_question(doc, chat_model)
        hypothetical_question_doc = Document(page_content=hypothetical_question, metadata={"original_doc": doc.page_content, **doc.metadata})
        hypothetical_questions.append(hypothetical_question_doc)
    
    from langchain_chroma import Chroma
    # 使用假设性问题构建向量数据库
    vectorstore = Chroma.from_documents(hypothetical_questions, embedding=embeddings_model, persist_directory="data/hypothetical_chroma")
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})
    
    # 生成查询的假设性回答向量
    hypothetical_answer = generate_hypothetical_answer(question, chat_model)
    print("Generated Hypothetical Answer: ", hypothetical_answer)
    # 将假设性回答转换为向量
    hypothetical_embedding = embeddings_model.embed_query(hypothetical_answer)
     # 使用向量进行相似性搜索
    retrieved_docs = vectorstore.similarity_search_by_vector(hypothetical_embedding, k=6)

    # 提取检索到的原始文档上下文
    combined_context = "\n\n".join([doc.metadata["original_doc"] for doc in retrieved_docs])
    
    from langchain import hub
    # currently single-round conversation; easy to implement conversation with context in the future
    prompt = hub.pull("rlm/rag-prompt")

    input_messages = prompt.invoke(
        {
            "context": combined_context, 
            "question": question
        }
    ).to_messages()

    print(chat_model.invoke(input=input_messages).content)
    print("相关链接：", retrieved_docs[0].metadata.get("url", "未提供"))