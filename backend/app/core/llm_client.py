"""
Cogent LLM Client Abstraction
Provides structured JSON generation via LLM when an API key is present,
with safe, graceful fallback to deterministic extractors when offline or unconfigured.
"""

import json
from typing import Optional, Dict, Any
from app.config import settings


class LLMClient:
    """
    Unified LLM Client supporting Google Gemini, Groq, and OpenAI via OpenAI-compatible endpoints,
    with safe, graceful fallback to deterministic extractors when offline or unconfigured.
    """

    def __init__(self):
        self._client = None
        self.provider = settings.LLM_PROVIDER
        self.api_key = ""
        self.base_url = None
        self.model = settings.OPENAI_MODEL

        # Determine active provider
        if self.provider == "gemini" or (self.provider == "auto" and settings.GEMINI_API_KEY):
            self.provider = "gemini"
            self.api_key = settings.GEMINI_API_KEY
            self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            self.model = settings.GEMINI_MODEL or "gemini-2.0-flash"
        elif self.provider == "groq" or (self.provider == "auto" and settings.GROQ_API_KEY):
            self.provider = "groq"
            self.api_key = settings.GROQ_API_KEY
            self.base_url = "https://api.groq.com/openai/v1"
            self.model = settings.GROQ_MODEL
        elif self.provider == "openai" or (self.provider == "auto" and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-placeholder"):
            self.provider = "openai"
            self.api_key = settings.OPENAI_API_KEY
            self.base_url = settings.OPENAI_BASE_URL or None
            self.model = settings.OPENAI_MODEL
        else:
            self.provider = "offline"

        self._is_configured = bool(self.api_key and self.api_key != "sk-placeholder" and self.provider != "offline")

    def _get_client(self):
        if not self._is_configured:
            return None
        if self._client is None:
            try:
                # pyrefly: ignore [missing-import]
                from openai import OpenAI
                kwargs = {"api_key": self.api_key, "timeout": 20.0}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                self._client = OpenAI(**kwargs)
            except Exception:
                self._client = None
        return self._client

    def _call_gemini_rest(
        self,
        system_prompt: str,
        user_prompt: str,
        response_json: bool = False,
        max_tokens: int = 500,
    ) -> Optional[str]:
        """
        Direct REST call to Google Generative Language API for robust, high-speed synthesis.
        Immediately returns None on 429 quota limits so deterministic fallback takes over without delay.
        """
        if not (self.provider == "gemini" and self.api_key):
            return None
        import httpx
        target_model = (self.model or "gemini-3.8-flash").replace("models/", "")
        # Fallback chain if primary model fails with 404
        models_to_try = [target_model]
        if target_model not in ("gemini-3.8-flash",):
            models_to_try.append("gemini-3.8-flash")

        import time
        for m_clean in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_clean}:generateContent?key={self.api_key}"
            payload: Dict[str, Any] = {
                "contents": [{"parts": [{"text": user_prompt}]}],
                "generationConfig": {
                    "temperature": 0.0 if response_json else 0.2,
                    "maxOutputTokens": max_tokens,
                },
            }
            if system_prompt:
                payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
            if response_json:
                payload["generationConfig"]["responseMimeType"] = "application/json"

            # Retry up to 3 times on 503 (model overloaded) with backoff
            for attempt in range(3):
                try:
                    with httpx.Client(timeout=25.0) as client:
                        resp = client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                # Find the last part with text or non-thought text
                                for p in reversed(parts):
                                    if "text" in p and p["text"].strip() and not p.get("thought", False):
                                        return p["text"].strip()
                                for p in parts:
                                    if "text" in p and p["text"].strip():
                                        return p["text"].strip()
                            break  # 200 but no content, move to next model
                        elif resp.status_code == 503:
                            # Model overloaded — wait and retry
                            if attempt < 2:
                                time.sleep(2 ** attempt)  # 1s, 2s
                                continue
                            else:
                                break  # Max retries on 503, try next model
                        else:
                            break  # 404 or other error, try next model
                except Exception:
                    break
        return None

    def generate_structured_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema_name: str = "structured_response",
    ) -> Optional[Dict[str, Any]]:
        """
        Generate structured JSON from the LLM.
        Returns None if LLM is not configured, unreachable, or fails,
        allowing calling sub-modules to use deterministic fallback.
        """
        if self.provider == "gemini":
            rest_res = self._call_gemini_rest(system_prompt, user_prompt, response_json=True, max_tokens=1000)
            if rest_res:
                try:
                    return json.loads(rest_res)
                except Exception:
                    pass
            return None

        client = self._get_client()
        if client is None:
            return None

        models_to_try = [self.model]
        for target_model in models_to_try:
            try:
                response = client.chat.completions.create(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                    timeout=5.0,
                )
                content = response.choices[0].message.content
                if content:
                    return json.loads(content)
            except Exception:
                continue
        return None

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 500,
    ) -> Optional[str]:
        """
        Generate fluent natural language text from the LLM.
        Returns None on any error or if offline, allowing clean deterministic fallback.
        """
        if self.provider == "gemini":
            rest_res = self._call_gemini_rest(system_prompt, user_prompt, response_json=False, max_tokens=max_tokens)
            if rest_res and len(rest_res.strip()) > 5:
                return rest_res.strip()
            return None

        client = self._get_client()
        if client is None:
            return None

        models_to_try = [self.model]
        for target_model in models_to_try:
            try:
                response = client.chat.completions.create(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens,
                    timeout=5.0,
                )
                content = response.choices[0].message.content
                if content:
                    return content.strip()
            except Exception as e:
                import traceback
                print(f"Groq API Error: {e}")
                traceback.print_exc()
                continue
        return None



