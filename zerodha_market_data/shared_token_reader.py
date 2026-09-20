from pathlib import Path


def read_shared_access_token(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Shared Zerodha access-token file not found: {path}")
    value = path.read_text(encoding="utf-8").strip()
    for key in ("ACCESS_TOKEN", "ZERODHA_ACCESS_TOKEN", "TOKEN"):
        if value.startswith(key + "="):
            value = value.split("=", 1)[1].strip()
            break
    if not value:
        raise ValueError("Shared Zerodha access-token file is empty.")
    return value
