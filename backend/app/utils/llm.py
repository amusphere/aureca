import openai
from pydantic import BaseModel

_openai_client: openai.OpenAI | None = None

DEFAULT_MODEL = "gpt-4.1"


def get_openai_client():
    """
    OpenAIのクライアントを取得するヘルパー関数
    """
    global _openai_client
    if _openai_client is None:
        from app.config.app import OpenAIConfig

        api_key = OpenAIConfig.API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables.")
        _openai_client = openai.OpenAI(api_key=api_key)
    return _openai_client


def llm_chat_completions(
    prompts: list[dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> str:
    client = get_openai_client()
    response = client.chat.completions.create(
        model=model,
        messages=prompts,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


def llm_chat_completions_perse(
    prompts: list[dict[str, str]],
    response_format: BaseModel,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> BaseModel:
    client = get_openai_client()
    response = client.beta.chat.completions.parse(
        model=model,
        messages=prompts,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format=response_format,
    )
    return response.choices[0].message.parsed
