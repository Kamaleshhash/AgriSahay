from backend.models.scheme import load_schemes


def list_schemes() -> list[dict[str, object]]:
    return [scheme.as_dict() for scheme in load_schemes()]