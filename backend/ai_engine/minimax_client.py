import json, logging
import httpx
from config.settings import settings
from backend.ai_engine.prompts import build_system_prompt
from backend.tool_modules.executor import TOOL_COMMANDS

log = logging.getLogger("minimax")

def _extract_json(content: str) -> dict:
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no json object found")
    return json.loads(content[start:end + 1])

class MinimaxClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=90.0)
        self.endpoint = settings.minimax_endpoint

    async def chat(self, user_message: str, tier: str, allowed_tools: list[str]) -> dict:
        if not settings.minimax_api_key:
            return {"reply": "MiniMax M3 not configured (MINIMAX_API_KEY missing). Contact admin."}
        system = build_system_prompt(allowed_tools, tier)
        payload = {
            "model": settings.minimax_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.2,
            "max_tokens": 8192,
        }
        headers = {"Authorization": "Bearer " + settings.minimax_api_key}
        try:
            r = await self.client.post(self.endpoint, json=payload, headers=headers)
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return {"reply": "MiniMax error: " + str(e)}
        try:
            data = json.loads(content)
        except Exception:
            try:
                data = _extract_json(content)
            except Exception:
                return {"reply": content}
        tr = data.get("tool_request")
        if isinstance(tr, dict) and str(tr.get("tool", "")).lower() in TOOL_COMMANDS:
            args = tr.get("args", [])
            tr["args"] = [str(a) for a in args] if isinstance(args, list) else []
            return {"reply": data.get("reply", "Tool request queued."), "tool_request": tr}
        return {"reply": data.get("reply", "I received your message.")}

minimax = MinimaxClient()