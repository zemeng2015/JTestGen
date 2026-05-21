from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


class GenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class GenerationRequest:
    system_prompt: str
    user_prompt: str


class OpenAICompatibleGenerator:
    def __init__(self, model_override: str | None = None) -> None:
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model_override or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate(self, request: GenerationRequest) -> str:
        if not self.api_key:
            raise GenerationError("OPENAI_API_KEY is required unless --dry-run is used.")

        payload = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        http_request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=120) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise GenerationError(f"Generation request failed: HTTP {exc.code}: {detail}") from exc
        except OSError as exc:
            raise GenerationError(f"Generation request failed: {exc}") from exc

        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GenerationError(f"Unexpected generation response: {body}") from exc

