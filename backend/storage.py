from pathlib import Path
import base64, uuid
from config.settings import settings

SELFIES_DIR = Path(settings.selfies_dir)
SELFIES_DIR.mkdir(parents=True, exist_ok=True)

def save_selfie(data_b64: str, prefix: str) -> str:
    raw = base64.b64decode(data_b64.split(",")[-1])
    name = f"{prefix}_{uuid.uuid4().hex[:8]}.jpg"
    (SELFIES_DIR / name).write_bytes(raw)
    return f"/selfies/{name}"
