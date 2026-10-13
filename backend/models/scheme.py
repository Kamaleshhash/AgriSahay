from dataclasses import dataclass
from pathlib import Path
import csv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEME_DATA = PROJECT_ROOT / "data" / "schemes.csv"


@dataclass(frozen=True)
class Scheme:
    id: str
    name: str
    level: str
    states: tuple[str, ...]
    crops: tuple[str, ...]
    needs: tuple[str, ...]
    summary: str
    eligibility_notes: str
    required_documents: tuple[str, ...]
    source_url: str
    verification_status: str
    last_verified: str

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "states": list(self.states),
            "crops": list(self.crops),
            "needs": list(self.needs),
            "summary": self.summary,
            "eligibility_notes": self.eligibility_notes,
            "required_documents": list(self.required_documents),
            "source_url": self.source_url,
            "verification_status": self.verification_status,
            "last_verified": self.last_verified,
        }


def load_schemes(path: Path = SCHEME_DATA) -> list[Scheme]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required_columns = {
            "id",
            "name",
            "level",
            "states",
            "crops",
            "needs",
            "summary",
            "eligibility_notes",
            "required_documents",
            "source_url",
            "verification_status",
            "last_verified",
        }
        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            raise ValueError(f"{path} is missing required scheme catalog columns.")
        schemes = []
        for row in reader:
            if not row.get("id") or not row.get("name"):
                raise ValueError(f"{path} contains a scheme row without an id or name.")
            schemes.append(
                Scheme(
                    id=row["id"].strip(),
                    name=row["name"].strip(),
                    level=row["level"].strip(),
                    states=_split(row["states"]),
                    crops=_split(row["crops"]),
                    needs=_split(row["needs"]),
                    summary=row["summary"].strip(),
                    eligibility_notes=row["eligibility_notes"].strip(),
                    required_documents=_split(row["required_documents"]),
                    source_url=row["source_url"].strip(),
                    verification_status=row["verification_status"].strip().lower(),
                    last_verified=row["last_verified"].strip(),
                )
            )
        return schemes


def _split(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split("|") if part.strip())