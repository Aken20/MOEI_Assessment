"""
ai/client.py
OpenRouter API client. Reads OPENROUTER_API_KEY and OPENROUTER_MODEL
from environment variables (never hardcoded).
Supports both OpenAI-compatible /v1/chat/completions and
Anthropic-style endpoints.
"""

import os
import json
from pathlib import Path
from typing import Optional

client: Optional[object] = None
_default_model = "deepseek/deepseek-v4-pro"


def _load_api_key() -> str:
    """Load API key from env first, then .env file as fallback."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key

    # Try .env file in project root
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path, override=False)
        except ImportError:
            # Manual parse if python-dotenv not installed
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        key = os.environ.get("OPENROUTER_API_KEY")

    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY not found. Set it in your environment or in the .env file. "
            "Copy .env.example to .env and add your key."
        )
    return key


def get_client():
    global client
    if client is None:
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

        api_key = _load_api_key()

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    return client


def complete(
    prompt: str,
    system: str = "",
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
    json_mode: bool = False,
) -> str:
    """
    Send a chat completion to OpenRouter.

    Returns the raw response content (string).
    Raises on API error.
    """
    client = get_client()
    model = model or os.environ.get("OPENROUTER_MODEL", _default_model)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def complete_structured(
    prompt: str,
    system: str = "",
    schema: dict = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 1536,
) -> dict:
    """
    Send a completion and parse the response as JSON.
    schema: a JSON-schema-like dict describing the expected structure.
    The system prompt instructs the model to output valid JSON matching the schema.
    """
    import json as _json

    client = get_client()
    model = model or os.environ.get("OPENROUTER_MODEL", _default_model)

    schema_str = _json.dumps(schema) if schema else '{"type": "object"}'

    system_prompt = (
        (system + "\n\n" if system else "")
        + f"Output ONLY valid JSON matching this schema (no markdown, no explanation):\n{schema_str}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("Model returned empty response — possible rate limit or content filter.")

    raw = content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
        raw = raw.rstrip("`").rstrip()

    # If the model returned text + JSON mixed, extract the JSON object
    if not raw.startswith("{"):
        # Find the first { and last }
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start:end + 1]
        else:
            raise RuntimeError(f"Model returned non-JSON response: {raw[:200]}...")

    return _json.loads(raw)