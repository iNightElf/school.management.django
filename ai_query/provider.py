import json
import logging
from abc import ABC, abstractmethod
from django.conf import settings

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    @abstractmethod
    def execute(self, system_prompt, user_query, functions):
        ...

    def build_function_definitions(self, functions):
        return [{
            "name": f["name"],
            "description": f["description"],
            "parameters": f["parameters"],
        } for f in functions]


class GeminiProvider(AIProvider):
    def __init__(self, api_key, model=None):
        self.api_key = api_key
        self.model = model or 'gemini-2.5-flash-lite'

    def execute(self, system_prompt, user_query, functions):
        if not self.api_key:
            return None
        try:
            import urllib.request
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/"
                f"models/{self.model}:generateContent?key={self.api_key}"
            )
            contents = []
            if system_prompt:
                contents.append({"role": "user", "parts": [{"text": system_prompt}]})
                contents.append({"role": "model", "parts": [{"text": "Understood."}]})
            contents.append({"role": "user", "parts": [{"text": user_query}]})

            payload = json.dumps({
                "contents": contents,
                "tools": [{"functionDeclarations": functions}],
            }).encode()

            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())

            candidate = result.get("candidates", [{}])[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            for part in parts:
                if "functionCall" in part:
                    fc = part["functionCall"]
                    return {"type": "function_call", "name": fc.get("name"), "args": fc.get("args", {})}
                if "text" in part:
                    return {"type": "text", "text": part["text"]}

            return {"type": "text", "text": ""}
        except Exception as e:
            logger.warning(f"Gemini API error: {e}")
            return None


class OpenAICompatibleProvider(AIProvider):
    def __init__(self, api_key, model=None, base_url=None):
        self.api_key = api_key
        self.model = model or 'deepseek-chat'
        self.base_url = (base_url or 'https://api.deepseek.com/v1').rstrip('/')

    def build_function_definitions(self, functions):
        return [{
            "type": "function",
            "function": {
                "name": f["name"],
                "description": f["description"],
                "parameters": f["parameters"],
            }
        } for f in functions]

    def execute(self, system_prompt, user_query, functions):
        if not self.api_key:
            return None
        try:
            import urllib.request
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_query})

            payload = json.dumps({
                "model": self.model,
                "messages": messages,
                "tools": functions,
                "tool_choice": "auto",
            }).encode()

            url = f"{self.base_url}/chat/completions"
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())

            choice = result.get("choices", [{}])[0]
            msg = choice.get("message", {})

            if tool_calls := msg.get("tool_calls"):
                tc = tool_calls[0]
                fn = tc.get("function", {})
                try:
                    args = json.loads(fn.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                return {"type": "function_call", "name": fn.get("name"), "args": args}

            if content := msg.get("content"):
                return {"type": "text", "text": content}

            return {"type": "text", "text": ""}
        except Exception as e:
            logger.warning(f"OpenAI API error: {e}")
            return None


def get_provider():
    provider_name = getattr(settings, 'AI_PROVIDER', 'gemini').lower()
    api_key = getattr(settings, 'AI_API_KEY', '') or getattr(settings, 'GEMINI_API_KEY', '')
    model = getattr(settings, 'AI_MODEL', '') or None
    base_url = getattr(settings, 'AI_API_BASE_URL', '') or None

    if provider_name == 'openai':
        return OpenAICompatibleProvider(api_key=api_key, model=model, base_url=base_url)

    return GeminiProvider(api_key=api_key, model=model)
