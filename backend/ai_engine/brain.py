import json, logging
import httpx
from config.settings import settings
from backend.ai_engine.prompts import build_system_prompt
from backend.tool_modules.executor import TOOL_COMMANDS

log = logging.getLogger("brain")

class Brain:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.base = settings.llm_endpoint

    async def chat(self, user_message: str, tier: str, allowed_tools: list[str]) -> dict:
        if not settings.llm_api_key:
            return {"reply": "AI brain not configured (LLM_API_KEY missing). Contact admin."}
        system = build_system_prompt(allowed_tools, tier)
        url = self.base + "/models/" + settings.llm_model + ":generateContent"
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user_message}]}],
            "generationConfig": {
                "temperature": 0.2,
                "response_mime_type": "application/json",
            },
        }
        headers = {"x-goog-api-key": settings.llm_api_key}
        try:
            r = await self.client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            resp = r.json()
            content = resp["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return {"reply": f"Brain error: {e}"}
        try:
            parsed = json.loads(content)
        except Exception:
            return {"reply": content}
        tr = parsed.get("tool_request")
        if isinstance(tr, dict) and str(tr.get("tool", "")).lower() in TOOL_COMMANDS:
            args = tr.get("args", [])
            tr["args"] = [str(a) for a in args] if isinstance(args, list) else []
            return {"reply": parsed.get("reply", "Tool request queued."), "tool_request": tr}
        return {"reply": parsed.get("reply", "I received your message.")}

brain = Brain()