import json
import time
from enum import Enum
from typing import Any, Dict

from openai import APIError, OpenAI, RateLimitError


class ChatGPTModels(Enum):
    GPT4oMini = "gpt-4o-mini"                 # ← cheapest file‑aware model
    # GPT4o     = "gpt-4o-2024-05-13"
    # GPT35Turbo = "gpt-3.5-turbo"


def send_prompt(
    client: OpenAI,
    prompt: str,
    system_message: str,
    retries: int = 1,
    model: ChatGPTModels = ChatGPTModels.GPT4oMini,   # ← new default
    prompt_options: Dict[str, Any] | None = None,
):
    """
    One‑shot chat completion with basic retry & JSON‑parsing.

    Returns JSON (dict / list) if the model responded with valid JSON,
    otherwise returns the raw text string; returns None on repeated failure.
    """

    default_options = {
        "temperature": 0,      # ← deterministic extraction
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }
    merged_options = {**default_options, **(prompt_options or {})}

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model.value,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                **merged_options,
            )

            content = (
                response.choices[0].message.content
                .strip()
                .lstrip("```json").rstrip("```")
                .strip()
            )

            if content.startswith("{") or content.startswith("["):
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    print("Warning: invalid JSON, returning raw text instead.")
                    return content
            return content

        except RateLimitError:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"Rate‑limited; retrying in {wait}s…")
                time.sleep(wait)
            else:
                print("Max retries reached (rate limit).")
                return None

        except APIError as e:
            print(f"OpenAI API error: {e}")
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"Retrying in {wait}s…")
                time.sleep(wait)
            else:
                print("Max retries reached (API error).")
                return None

        except Exception as e:
            print(f"Unexpected error: {e}")
            if attempt >= retries - 1:
                return None