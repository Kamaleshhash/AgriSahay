from backend.services.eligibility import match_schemes


def check_eligibility(profile: object) -> dict[str, object]:
    return match_schemes(profile)