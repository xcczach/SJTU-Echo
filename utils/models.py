from typing import Any
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, convert_to_openai_messages
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks import CallbackManagerForLLMRun

class QwenModel(BaseChatModel):
    model: str
    def __init__(self, model: str, gpu_memory_utilization: float = 0.6):
        super().__init__(model=model)
        quantization = None
        if "GPTQ" in model:
            quantization = "gptq"
        elif "AWQ" in model:
            quantization = "awq"
        self._model = LLM(model=model, quantization=quantization, gpu_memory_utilization=gpu_memory_utilization)
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