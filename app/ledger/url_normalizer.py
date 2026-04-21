def normalize_relay_url(value: str) -> str:
    v = value.strip().lower()
    if v.startswith("https://"):
        v = v[len("https://"):]
    elif v.startswith("http://"):
        v = v[len("http://"):]
    return v.rstrip("/")
