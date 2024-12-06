from langchain_chroma import Chroma
import json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.vectorstores import VectorStore
from langchain import hub
from typing import Literal
from timeit import default_timer as timer

from typing import Any
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, convert_to_openai_messages
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks import CallbackManagerForLLMRun

class QwenModel(BaseChatModel):
    model: str
    def __init__(self, model: str):
        super().__init__(model=model)
        self._model = LLM(model=model)
        self._tokenizer = AutoTokenizer.from_pretrained(self.model)

    def _generate(self, messages: list[BaseMessage], stop: list[str] | None = None, run_manager: CallbackManagerForLLMRun | None = None, **kwargs: Any) -> ChatResult:
        oai_messages = convert_to_openai_messages(messages)
        text = self._tokenizer.apply_chat_template(
            oai_messages,
            tokenize=False,
            add_generation_prompt=True
        )
        outputs = self._model.generate(
            [text],
            sampling_params = SamplingParams(temperature=0.7, top_p=0.8, repetition_penalty=1.05, max_tokens=512)
        )
        print(len(outputs))
        print(len(outputs[0].outputs))
        response_text = outputs[0].outputs[0].text
        response_message = AIMessage(
            content=response_text
        )
        response_generation = ChatGeneration(message=response_message)
        return ChatResult(generations=[response_generation])
    
    @property
    def _llm_type(self) -> str:
        return "qwen"
    
    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"model": self.model}

def timed(func):
    def wrapper(*args, **kwargs):
        start = timer()
        result = func(*args, **kwargs)
        end = timer()
        print(f"Time elapsed for {func.__name__}: {end - start} s")
        return result
    return wrapper

def get_hf_vectorstore(source_dir: str):
    with open(f"{source_dir}/embedding_metadata.json", "r") as f:
        embedding_model_name = json.load(f)["embedding_model_name"]
    embeddings_model = HuggingFaceEmbeddings(model_name=embedding_model_name, model_kwargs={"trust_remote_code": True})
    vectorstore = Chroma(embedding_function=embeddings_model, persist_directory=source_dir)
    return vectorstore

_strategy_hypothetical_question_prompt = hub.pull("rlm/rag-prompt")
def _get_answer_strategy_hypothetical_question(messages: list[BaseMessage], chat_model: BaseChatModel, vectorstore: VectorStore):
    @timed
    def generate_hypothetical_answer(question: str, chat_model) -> str:
        prompt_text = f"根据以下问题生成一个简洁的假设性回答，以便用于相似性检索优化：\n\n问题：{question}\n\n假设性回答："
        input_messages = [HumanMessage(content=prompt_text)]
        response = chat_model.invoke(input=input_messages).content
        return response.strip()
    question = messages[-1].content
    embeddings_model = vectorstore.embeddings
    hypothetical_answer = generate_hypothetical_answer(question, chat_model)
    @timed
    def embed_query(hypothetical_answer: str):
        return embeddings_model.embed_query(hypothetical_answer)
    hypothetical_embedding = embed_query(hypothetical_answer)
    @timed
    def similarity_search_by_vector(hypothetical_embedding, k=6):
        return vectorstore.similarity_search_by_vector(hypothetical_embedding, k=k)
    retrieved_docs = similarity_search_by_vector(hypothetical_embedding, k=6)
    combined_context = "\n\n".join([doc.metadata["original_doc"] for doc in retrieved_docs])
    input_messages = _strategy_hypothetical_question_prompt.invoke(
        {
            "context": combined_context, 
            "question": question
        }
    ).to_messages()
    new_messages = messages + input_messages
    @timed
    def chat_model_invoke(new_messages):
        return chat_model.invoke(input=new_messages)
    content = chat_model_invoke(new_messages).content
    return AIMessage(content=content, response_metadata={"link": retrieved_docs[0].metadata.get("url", "未提供")})

def inference(messages: list[BaseMessage], chat_model: BaseChatModel, vectorstore: VectorStore, strategy: Literal["hypothetical_question"]="hypothetical_question"):
    if strategy == "hypothetical_question":
        return _get_answer_strategy_hypothetical_question(messages, chat_model, vectorstore)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    
if  __name__ == "__main__":
    source_dir = "test_output/sample_embeddings"
    vectorstore = get_hf_vectorstore(source_dir)
    chat_model = QwenModel(model="Qwen/Qwen2.5-1.5B-Instruct-AWQ")
    messages = [HumanMessage(content="生医工的申报要求是什么？")]
    response = inference(messages, chat_model, vectorstore, strategy="hypothetical_question")
    print(response.content)
    print(response.response_metadata)