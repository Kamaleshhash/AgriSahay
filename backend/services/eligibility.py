from backend.models.farmer import normalize_profile
from backend.models.scheme import Scheme, load_schemes


def match_schemes(profile_payload: object) -> dict[str, object]:
    profile = normalize_profile(profile_payload)
    matches = []
    excluded = []

    for scheme in load_schemes():
        reasons = []
        conflicts = []
        state = profile["state"].casefold()
        if state and "all india" not in {item.casefold() for item in scheme.states}:
            if state not in {item.casefold() for item in scheme.states}:
                conflicts.append(f"Catalog lists {', '.join(scheme.states)}; your state is {profile['state']}.")

        crop = profile["crop"].casefold()
        if crop and "*" not in scheme.crops:
            if crop not in {item.casefold() for item in scheme.crops}:
                conflicts.append(f"Catalog lists crops {', '.join(scheme.crops)}; your crop is {profile['crop']}.")

        need = profile["need"]
        if need != "any" and need not in scheme.needs:
            conflicts.append(f"This catalog entry is not tagged for {need.replace('-', ' ')}.")

        if conflicts:
            excluded.append({"scheme_id": scheme.id, "name": scheme.name, "reasons": conflicts})
            continue

        if state:
            reasons.append(f"Listed for {', '.join(scheme.states)}; state availability still needs confirmation.")
        if crop:
            reasons.append(
                "Crop is within the catalog tags."
                if "*" in scheme.crops or crop in {item.casefold() for item in scheme.crops}
                else "Crop does not match the catalog tags; state/department rules may differ."
            )
        if need != "any":
            reasons.append(f"Scheme category matches your request for {need.replace('-', ' ')}.")
        if not reasons:
            reasons.append("Potentially relevant general agricultural support; confirm local availability.")

        missing_documents = [
            document
            for document in scheme.required_documents
            if document.casefold() not in {item.casefold() for item in profile["documents"]}
        ]
        if scheme.verification_status != "verified":
            documents_note = "The scheme-specific document checklist has not been verified; no missing-document conclusion is available."
        else:
            documents_note = "Confirm this checklist with the scheme portal before applying."

        matches.append(
            {
                "scheme": scheme.as_dict(),
                "relevance": "potential",
                "eligibility": "needs_review",
                "reasons": reasons,
                "mismatches": conflicts,
                "eligibility_note": (
                    "Eligibility has not been assessed. This catalog has no verified rules for "
                    "land size, ownership, farmer category, income, irrigation, or district-level availability."
                ),
                "missing_documents": missing_documents,
                "documents_note": documents_note,
                "next_action": _next_action(scheme),
            }
        )

    matches.sort(key=lambda item: _rank(item, profile))
    return {
        "profile": profile,
        "matches": matches,
        "excluded": excluded,
        "disclaimer": (
            "Guidance only, not an official eligibility decision. Catalog entries are leads, "
            "not verified scheme rules. Confirm eligibility, current enrollment, documents, "
            "and state-level availability with the linked department."
        ),
    }


def _rank(result: dict[str, object], profile: dict[str, object]) -> tuple[int, int, str]:
    scheme = result["scheme"]
    score = 0
    if profile["need"] in scheme["needs"]:
        score += 3
    if profile["state"] and profile["state"].casefold() in {state.casefold() for state in scheme["states"]}:
        score += 2
    if profile["crop"] and (
        "*" in scheme["crops"]
        or profile["crop"].casefold() in {crop.casefold() for crop in scheme["crops"]}
    ):
        score += 1
    return (-score, 0 if scheme["verification_status"] == "verified" else 1, scheme["name"])


def _next_action(scheme: Scheme) -> str:
    if scheme.verification_status != "verified":
        return "Open the official starting point and ask the local agriculture office to confirm current rules and availability."
    return "Review the official eligibility conditions and application window before applying."