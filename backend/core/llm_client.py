import asyncio
import json
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

import aiohttp
import tiktoken

_encoder = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_encoder.encode(text))


@dataclass
class GenerationConfig:
    temperature: float = 0.8
    max_tokens: int = 4000
    top_p: float = 0.9
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.1
    stop_sequences: list[str] = field(default_factory=list)

    def to_api_dict(self) -> dict:
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "stop": self.stop_sequences,
        }


class LMStudioClient:
    def __init__(self, base_url: str, model: str, timeout: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={"Content-Type": "application/json"},
        )

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    async def check_connection(self) -> dict:
        """Never raises - always returns a dict."""
        if not self._session:
            return {"connected": False, "error": "Client session not initialized"}
        try:
            async with self._session.get(f"{self.base_url}/models") as resp:
                data = await resp.json()
                models = data.get("data", [])
                active = models[0].get("id", "unknown") if models else "none"
                return {"connected": True, "models": models, "active_model": active}
        except Exception as e:  # noqa: BLE001
            return {"connected": False, "error": str(e)}

    async def generate_stream(
        self,
        messages: list[dict],
        config: Optional[GenerationConfig] = None,
    ) -> AsyncGenerator[str, None]:
        if not self._session:
            raise RuntimeError("LMStudioClient not initialized. Call initialize() first.")
        config = config or GenerationConfig()
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            **config.to_api_dict(),
        }
        try:
            async with self._session.post(
                f"{self.base_url}/chat/completions", json=payload
            ) as response:
                if response.status != 200:
                    body = await response.text()
                    raise ConnectionError(f"LM Studio returned {response.status}: {body[:200]}")
                async for raw_line in response.content:
                    line = raw_line.decode("utf-8").strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            chunk = delta.get("content")
                            if chunk:
                                yield chunk
                        except (json.JSONDecodeError, IndexError):
                            continue
        except aiohttp.ClientConnectorError as e:
            raise ConnectionError(
                "Cannot connect to LM Studio. "
                "Please open LM Studio, load a model, and click 'Start Server'."
            ) from e

    async def generate(
        self,
        messages: list[dict],
        config: Optional[GenerationConfig] = None,
    ) -> str:
        chunks: list[str] = []
        async for chunk in self.generate_stream(messages, config):
            chunks.append(chunk)
        return "".join(chunks)

    async def generate_structured(
        self,
        messages: list[dict],
        schema: dict,
        max_retries: int = 3,
    ) -> dict:
        schema_instruction = (
            "Respond ONLY with a valid JSON object matching this schema exactly.\n"
            "No markdown fences, no explanation, no preamble.\n"
            f"Schema:\n{json.dumps(schema, indent=2)}"
        )
        msgs = messages + [{"role": "system", "content": schema_instruction}]
        raw = ""

        for attempt in range(max_retries):
            try:
                raw = await self.generate(msgs, GenerationConfig(temperature=0.3))
                cleaned = raw.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[-1]
                if cleaned.endswith("```"):
                    cleaned = cleaned.rsplit("```", 1)[0]
                return json.loads(cleaned.strip())
            except json.JSONDecodeError as e:
                if attempt == max_retries - 1:
                    raise ValueError(
                        f"LLM returned invalid JSON after {max_retries} attempts. "
                        f"Last error: {e}. Last response: {raw[:300]}"
                    )
                msgs.append({"role": "assistant", "content": raw})
                msgs.append(
                    {
                        "role": "user",
                        "content": "That was not valid JSON. Respond with ONLY a JSON object.",
                    }
                )
                await asyncio.sleep(0.5 * (attempt + 1))

    def estimate_context_tokens(self, messages: list[dict]) -> int:
        total = 0
        for msg in messages:
            total += count_tokens(msg.get("content", ""))
            total += 4
        total += 2
        return total
