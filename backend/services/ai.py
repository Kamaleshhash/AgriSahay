import re
from typing import Any

from backend.models.farmer import normalize_profile
from backend.services.eligibility import match_schemes


CROP_TERMS = {
    "rice": ("rice", "paddy", "nel", "நெல்"),
    "sugarcane": ("sugarcane", "karumbu", "கரும்பு"),
    "cotton": ("cotton", "paruthi", "பருத்தி"),
    "maize": ("maize", "corn", "cholam", "மக்காச்சோளம்"),
    "groundnut": ("groundnut", "peanut", "verkadalai", "வேர்க்கடலை"),
    "banana": ("banana", "vaazhai", "வாழை"),
}

NEED_TERMS = {
    "income-support": ("income", "support", "cash", "benefit", "varumanam", "உதவி"),
    "crop-insurance": ("insurance", "kaappeetu", "காப்பீடு"),
    "irrigation": ("irrigation", "water", "drip", "sprinkler", "neer", "நீர்ப்பாசனம்"),
    "solar-energy": ("solar", "pump", "sooriya", "சூரிய"),
}


def answer_farmer(message: Any, profile_payload: Any = None, language: str = "en") -> dict[str, object]:
    if not isinstance(message, str) or not message.strip() or len(message) > 2_000:
        raise ValueError("Enter a question of 1 to 2,000 characters.")
    if profile_payload is not None and not isinstance(profile_payload, dict):
        raise ValueError("Profile must be a JSON object.")
    if language not in {"en", "ta", "tanglish"}:
        raise ValueError("Language must be en, ta, or tanglish.")
    profile = dict(profile_payload) if profile_payload is not None else {}
    lowered = message.casefold()

    if not profile.get("land_area_acres"):
        acreage = re.search(r"(\d+(?:\.\d+)?)\s*(?:acre|acres|ஏக்கர்|ekkar)", lowered)
        if acreage:
            profile["land_area_acres"] = acreage.group(1)
    if not profile.get("crop"):
        for crop, terms in CROP_TERMS.items():
            if any(_contains_term(lowered, term) for term in terms):
                profile["crop"] = crop
                break
    if profile.get("need", "any") == "any":
        for need, terms in NEED_TERMS.items():
            if any(_contains_term(lowered, term) for term in terms):
                profile["need"] = need
                break

    result = match_schemes(profile)
    names = [entry["scheme"]["name"] for entry in result["matches"][:3]]
    if language == "ta":
        intro = "உங்கள் தகவலின் அடிப்படையில் பார்க்கக்கூடிய திட்டங்கள்:"
        ending = "இவை ஆரம்ப வழிகாட்டுதல் மட்டுமே; அதிகாரப்பூர்வ தகுதியை சம்பந்தப்பட்ட துறையில் உறுதிப்படுத்தவும்."
    elif language == "tanglish":
        intro = "Unga details base-la check panna vendiya schemes:"
        ending = "Idhu guidance mattum; official eligibility-ai department kitta confirm pannunga."
    else:
        intro = "Potentially relevant schemes to check:"
        ending = "This is guidance only; confirm official eligibility with the department."
    return {
        "detected_profile": normalize_profile(profile),
        "scheme_names": names,
        "answer": f"{intro} {', '.join(names) if names else 'No catalog entries found yet.'} {ending}",
        "disclaimer": result["disclaimer"],
        "matches": result["matches"][:3],
        "mode": "keyword-assisted; no external AI service is called",
    }


def _contains_term(text: str, term: str) -> bool:
    if term.isascii():
        return re.search(rf"(?<!\w){re.escape(term.casefold())}(?!\w)", text) is not None
    return term.casefold() in text