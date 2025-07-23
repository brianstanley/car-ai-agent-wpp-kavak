from typing import Any, List, Dict, Protocol

class LLMClientProtocol(Protocol):
    def chat_completion(self, *, model: str, messages: List[Dict], **kwargs) -> Any:
        ...

    def embedding(self, *, model: str, input: Any, **kwargs) -> Any:
        ... 