def to_bool(s: str | bool) -> bool:
    return s.lower() in [True, 't', 'true', '1', 'ok', 'yes', 'on', 'enable', 'enabled', 'active']
