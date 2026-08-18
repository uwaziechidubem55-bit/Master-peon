import json, logging, os
import httpx
from config.settings import settings
from backend.ai_engine.prompts import build_system_prompt
from backend.tool_modules.executor import TOOL_COMMANDS

log = logging.getLogger("brain")

class Brain:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.endpoint = os.getenv("LLM_ENDPOINT", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions")

    async def chat(self, user_message: str, tier: str, allowed_tools: list[str]) -> dict:
        if not settings.llm_api_key:
            return {"reply": "AI brain not configured (LLM_API_KEY missing). Contact admin."}
        system = build_system_prompt(allowed_tools, tier)
        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
        try:
            r = await self.client.post(self.endpoint, json=payload, headers=headers)
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return {"reply": f"Brain error: {e}"}
        try:
            data = json.loads(content)
        except Exception:
            return {"reply": content}
        tr = data.get("tool_request")
        if isinstance(tr, dict) and str(tr.get("tool", "")).lower() in TOOL_COMMANDS:
            args = tr.get("args", [])
            tr["args"] = [str(a) for a in args] if isinstance(args, list) else []
            return {"reply": data.get("reply", "Tool request queued."), "tool_request": tr}
        return {"reply": data.get("reply", "I received your message.")}

brain = Brain()