from app.core.config import settings


class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.api_key = settings.LLM_API_KEY
        self.api_url = settings.LLM_API_URL
        self.model = settings.LLM_MODEL

    async def chat(self, system_prompt: str, user_prompt: str, response_format: dict = None):
        provider = self.provider.lower()

        if provider == "openai":
            return await self._openai_chat(system_prompt, user_prompt, response_format)
        elif provider in ("anthropic", "claude"):
            return await self._anthropic_chat(system_prompt, user_prompt, response_format)
        elif provider in ("ollama", "local"):
            return await self._ollama_chat(system_prompt, user_prompt, response_format)
        elif provider == "google":
            return await self._google_chat(system_prompt, user_prompt, response_format)
        elif provider == "groq":
            return await self._groq_chat(system_prompt, user_prompt, response_format)
        else:
            return await self._openai_compatible_chat(system_prompt, user_prompt, response_format)

    async def chat_stream(self, system_prompt: str, user_prompt: str):
        provider = self.provider.lower()
        if provider == "openai":
            async for chunk in self._openai_stream(system_prompt, user_prompt):
                yield chunk
        elif provider == "groq":
            async for chunk in self._groq_stream(system_prompt, user_prompt):
                yield chunk
        else:
            async for chunk in self._openai_stream(system_prompt, user_prompt):
                yield chunk

    async def _openai_stream(self, system_prompt: str, user_prompt: str):
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key, base_url=self.api_url)
        stream = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _groq_stream(self, system_prompt: str, user_prompt: str):
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key, base_url="https://api.groq.com/openai/v1")
        stream = await client.chat.completions.create(
            model=self.model or "llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _openai_chat(self, system_prompt: str, user_prompt: str, response_format: dict = None):
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key, base_url=self.api_url)
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if response_format:
            kwargs["response_format"] = response_format
        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def _anthropic_chat(self, system_prompt: str, user_prompt: str, response_format: dict = None):
        import httpx
        async with httpx.AsyncClient() as client:
            body = {
                "model": self.model or "claude-3-5-sonnet-20241022",
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            }
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            url = self.api_url or "https://api.anthropic.com/v1/messages"
            resp = await client.post(url, json=body, headers=headers)
            data = resp.json()
            return data.get("content", [{}])[0].get("text", "")

    async def _ollama_chat(self, system_prompt: str, user_prompt: str, response_format: dict = None):
        import httpx
        async with httpx.AsyncClient() as client:
            body = {
                "model": self.model or "llama3.2",
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            url = (self.api_url or "http://localhost:11434") + "/api/chat"
            resp = await client.post(url, json=body)
            data = resp.json()
            return data.get("message", {}).get("content", "")

    async def _google_chat(self, system_prompt: str, user_prompt: str, response_format: dict = None):
        import httpx
        async with httpx.AsyncClient() as client:
            body = {
                "contents": [{"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096},
            }
            key = self.api_key or "DEMO_KEY"
            model = self.model or "gemini-2.0-flash"
            base = self.api_url or "https://generativelanguage.googleapis.com/v1beta"
            url = f"{base}/models/{model}:generateContent?key={key}"
            resp = await client.post(url, json=body)
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            error = data.get("error", {}).get("message", "")
            if error:
                return f"[Gemini API error: {error}]"
            return ""

    async def _groq_chat(self, system_prompt: str, user_prompt: str, response_format: dict = None):
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key, base_url="https://api.groq.com/openai/v1")
        kwargs = {
            "model": self.model or "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if response_format:
            kwargs["response_format"] = response_format
        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def _openai_compatible_chat(self, system_prompt: str, user_prompt: str, response_format: dict = None):
        from openai import AsyncOpenAI
        if not self.api_url:
            self.api_url = "https://api.openai.com/v1"
        client = AsyncOpenAI(api_key=self.api_key, base_url=self.api_url)
        kwargs = {
            "model": self.model or "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if response_format:
            kwargs["response_format"] = response_format
        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


llm = LLMClient()
