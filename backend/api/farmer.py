from backend.models.farmer import normalize_profile


def validate_profile(payload: object) -> dict[str, object]:
    return normalize_profile(payload)