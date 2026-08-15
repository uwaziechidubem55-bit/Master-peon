from sqlalchemy.orm import Session
from backend import models

DEFAULT_RULES = [
    "No scanning of government, military, banking, or social-media domains.",
    "No credential harvesting, phishing, or spam.",
    "No sharing of scan results publicly.",
    "No attempts to access admin paths.",
]

def current_rules(db: Session) -> list[str]:
    rules = db.query(models.PolicyRule).filter(models.PolicyRule.active).all()
    return [r.text for r in rules] or DEFAULT_RULES

def check_request(args: list[str], db: Session) -> tuple[bool, str]:
    joined = " ".join(args).lower()
    for text in current_rules(db):
        for word in text.lower().split():
            w = word.strip(".,;:()")
            if w and w in joined:
                return False, text
    return True, ""
