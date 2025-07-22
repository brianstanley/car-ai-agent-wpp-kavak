from services.llm_protocol import LLMClientProtocol
from openai import OpenAI
from typing import Any, List, Dict

class OpenAIClientAdapter(LLMClientProtocol):
    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key)

    def chat_completion(self, *, model: str, messages: List[Dict], **kwargs) -> Any:
        return self.client.chat.completions.create(model=model, messages=messages, **kwargs)

    def embedding(self, *, model: str, input: Any, **kwargs) -> Any:
        return self.client.embeddings.create(model=model, input=input, **kwargs) 