from typing import Any


ALLOWED_OWNERSHIP = {"owned", "leased", "shared", "unknown"}
ALLOWED_NEEDS = {
    "any",
    "income-support",
    "crop-insurance",
    "irrigation",
    "solar-energy",
}
MAX_DOCUMENTS = 50
MAX_DOCUMENT_NAME_LENGTH = 100


class ProfileError(ValueError):
    pass


def normalize_profile(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ProfileError("Profile must be a JSON object.")

    state = _text(payload, "state", max_length=80)
    crop = _text(payload, "crop", max_length=80)
    ownership = _text(payload, "ownership", max_length=20).lower() or "unknown"
    need = _text(payload, "need", max_length=40).lower() or "any"
    irrigation = _text(payload, "irrigation", max_length=80)
    farmer_category = _text(payload, "farmer_category", max_length=80)
    activity = _text(payload, "activity", max_length=80)

    if ownership not in ALLOWED_OWNERSHIP:
        raise ProfileError("Ownership must be owned, leased, shared, or unknown.")
    if need not in ALLOWED_NEEDS:
        raise ProfileError("Choose a supported scheme category.")

    land_area = payload.get("land_area_acres")
    if land_area in (None, ""):
        land_area = None
    else:
        try:
            land_area = float(land_area)
        except (TypeError, ValueError) as error:
            raise ProfileError("Land area must be a number of acres.") from error
        if not 0 <= land_area <= 100_000:
            raise ProfileError("Land area must be between 0 and 100,000 acres.")

    documents = payload.get("documents", [])
    if not isinstance(documents, list) or any(not isinstance(item, str) for item in documents):
        raise ProfileError("Documents must be a list of names.")
    if len(documents) > MAX_DOCUMENTS or any(len(item) > MAX_DOCUMENT_NAME_LENGTH for item in documents):
        raise ProfileError("Provide no more than 50 document names, each up to 100 characters.")

    return {
        "state": state,
        "district": _text(payload, "district", max_length=80),
        "land_area_acres": land_area,
        "ownership": ownership,
        "crop": crop,
        "farmer_category": farmer_category,
        "irrigation": irrigation,
        "activity": activity,
        "need": need,
        "documents": [item.strip() for item in documents if item.strip()],
    }


def _text(payload: dict[str, Any], key: str, max_length: int) -> str:
    value = payload.get(key, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ProfileError(f"{key.replace('_', ' ').capitalize()} must be text.")
    value = value.strip()
    if len(value) > max_length:
        raise ProfileError(f"{key.replace('_', ' ').capitalize()} is too long.")
    return value