import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def call_gemini_with_functions(system_prompt, user_query, functions):
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        return None
    try:
        import urllib.request
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/gemini-2.0-flash:generateContent?key={api_key}"
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

        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
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
        logger.warning(f"Gemini function-calling error: {e}")
        return None


def build_function_definitions(registry_slice):
    fns = []
    for entry in registry_slice:
        fns.append({
            "name": entry["name"],
            "description": entry["description"],
            "parameters": entry["parameters"],
        })
    return fns
