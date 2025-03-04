"""
Configuration management for vim-genius.
"""

import os

from dotenv import load_dotenv
from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai_bedrock.bedrock import BedrockModel


def load_config() -> None:
    """
    Load configuration from ~/.vim_genius file into environment variables.
    """
    # Config file is in user home directory
    config_file = os.path.expanduser("~/.vim_genius")
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    # Load environment variables from config file
    load_dotenv(config_file)


def validate_config() -> None:
    """Validate configuration settings."""
    api_family = os.getenv("API_FAMILY", "")
    model_name = os.getenv("MODEL_NAME", "")
    model_api_key = os.getenv("MODEL_API_KEY", "")

    if not api_family or not model_name:
        raise ValueError("API_FAMILY and MODEL_NAME must be set in ~/.vim_genius")

    if api_family != "bedrock" and not model_api_key:
        raise ValueError("MODEL_API_KEY must be set in ~/.vim_genius for non-bedrock APIs")


def create_model(api_family: str, model_name: str, api_key: str) -> Model:
    """
    Create a model instance based on the API family.

    Args:
        api_family: The API family (openai, anthropic, bedrock, openrouter)
        model_name: The name of the model to use
        api_key: The API key for authentication

    Returns:
        A model instance

    Raises:
        ValueError: If the API family is unknown
    """
    match api_family:
        case "openai":
            return OpenAIModel(model_name, api_key=api_key)
        case "anthropic":
            return AnthropicModel(model_name, api_key=api_key)
        case "bedrock":
            return BedrockModel(model_name)
        case "openrouter":
            return OpenAIModel(
                model_name,
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
            )
        case _:
            raise ValueError(f"Unknown model api family: {api_family}")
