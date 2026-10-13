from backend.services.ai import answer_farmer


def ask_assistant(message: object, profile: object = None, language: str = "en") -> dict[str, object]:
    return answer_farmer(message, profile, language)