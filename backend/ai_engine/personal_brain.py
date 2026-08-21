import re
from backend.ai_engine.brain import brain
from backend.ai_engine.minimax_client import minimax
from backend.ai_engine.pentest_brain import detect, answer as pentest_answer

REFUSAL_MARKERS = [
    "i cannot", "i can't", "i won't", "i'm sorry", "i am sorry",
    "cannot assist", "can't assist", "not able to", "unable to",
    "against my", "not allowed", "do not feel comfortable",
    "as an ai", "as a language model", "i don't feel comfortable",
    "sorry, but", "i apologize, but", "i'm not able", "i am not able",
    "cannot help", "can't help", "refuse",
]

IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
URL_RE = re.compile(r"https?://[^\s]+")
TOOL_RE = re.compile(r"\b(nmap|nikto|sqlmap|hydra|hashcat|tcpdump|dirb|ffuf|whatweb|sublist3r|netcat|tshark|whois|medusa|crunch|routersploit|burp|metasploit|netdiscover|linpeas|winpeas|pspy|chisel|ligolo|john)\b")

def _score(text: str, has_tool: bool) -> int:
    if not text:
        return -1000
    low = text.lower()
    score = 0
    for marker in REFUSAL_MARKERS:
        if marker in low:
            score -= 150
    if low.startswith("brain error") or low.startswith("minimax error"):
        score -= 500
    length = len(text)
    if length < 40:
        score -= 20
    elif length < 8000:
        score += min(length // 20, 60)
    else:
        score += 60
    score += text.count("```") * 8
    score += min(text.count("\n"), 20)
    score += len(TOOL_RE.findall(low)) * 6
    score += len(URL_RE.findall(text)) * 4
    score += len(IP_RE.findall(text)) * 3
    if has_tool:
        score += 40
    return score

class PersonalBrain:
    async def chat(self, user_message: str, tier: str, allowed_tools: list[str]) -> dict:
        if detect(user_message):
            return pentest_answer(user_message)
        gemini_result = await brain.chat(user_message, tier, allowed_tools)
        minimax_result = await minimax.chat(user_message, tier, allowed_tools)
        gemini_score = _score(gemini_result.get("reply", ""), bool(gemini_result.get("tool_request")))
        minimax_score = _score(minimax_result.get("reply", ""), bool(minimax_result.get("tool_request")))
        if minimax_score > gemini_score:
            return minimax_result
        return gemini_result

personal_brain = PersonalBrain()