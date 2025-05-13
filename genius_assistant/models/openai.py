"""
Customization of pydantic a OpenAI model that fixes issues with OpenRouter:

    - https://github.com/pydantic/pydantic-ai/issues/527
"""

from openai.types import chat
from pydantic_ai.messages import (
    ModelResponse,
)
from pydantic_ai.models.openai import OpenAIModel


class GeniusOpenAIModel(OpenAIModel):
    def _process_response(self, response: chat.ChatCompletion) -> ModelResponse:
        if hasattr(response, "error") and "message" in response.error:
            raise ValueError(response.error["message"])
        return super()._process_response(response)
