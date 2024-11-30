with open("contexts.txt", "r") as f:
    contexts = f.readlines()
contexts = [context.strip() for context in contexts]
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel, SimpleChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, convert_to_openai_messages
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.runnables import run_in_executor
from transformers import AutoModelForCausalLM, AutoTokenizer
import re

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
    
chat_model = QwenModel(model="Qwen/Qwen2.5-1.5B-Instruct")
questions = []
def remove_non_chinese_characters(text):
    """
    去除字符串中所有非中文字符

    参数:
        text (str): 输入字符串

    返回:
        str: 仅包含中文字符的字符串
    """
    chinese_characters = re.findall(r'[\u4e00-\u9fff]+', text)
    return ''.join(chinese_characters)
for context in contexts:
    context = remove_non_chinese_characters(context)
    if len(context) == 0:
        continue
    question = chat_model.invoke(f""":针对Context提出一个问题，需要提到Context主题本身，不要提到“这”、“此”等指示代词，使用“请问”开头，仅仅回复问题：
                                 Context: {context}""").content
    questions.append(question)
    print(question)
with open("sample_questions.txt", "w") as f:
    f.write("\n".join(questions))