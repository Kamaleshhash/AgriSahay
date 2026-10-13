# AgriSahay

AgriSahay is a farmer-guidance MVP for discovering potentially relevant agricultural schemes and getting a simple crop-data suggestion. It is **not** an official eligibility checker and does not replace government departments.

## Run locally

Requires Python 3.10 or later and the packages listed in `backend/requirements.txt`.

```powershell
python -m pip install -r backend/requirements.txt
python -m backend.main
```

Open <http://127.0.0.1:8000>. Set `AGRISAHAY_HOST` and `AGRISAHAY_PORT` to change the bind address and port.

## What it does

- Collects state, district, land area, ownership, crop, farmer category, irrigation and support need.
- Ranks catalog leads and explains why each might be relevant.
- Offers an assistant that extracts a small set of English, Tamil and Tanglish crop/need terms from a question.
- Suggests a crop using the trained classifier in `ai_ml/models/crop_recommendation_model.pkl`.
- Serves a responsive English/Tamil/Tanglish interface from the same local server.

## Scheme catalog safety

`data/schemes.csv` is a **starter lead list**, not a verified rules database. Every initial record is marked `unverified`; rule fields are intentionally not presented as official requirements, and the app returns `needs_review` rather than saying a farmer is eligible or ineligible. Scheme-specific document checklists are blank until confirmed. The linked official portals are starting points; confirm the current scheme, state availability, conditions, application window and documents with the department before applying.

Do not change a record's `verification_status` to `verified` until a maintainer has checked its current source, eligibility rules, documents and active application details. Even then, this MVP does not evaluate scheme-specific eligibility rules; it will continue to return `needs_review`. Fill `last_verified` with the review date (`YYYY-MM-DD`) when catalog data is reviewed. Do not use the app to make or imply an official determination.

## API

- `GET /health`
- `GET /api/schemes`
- `POST /api/match` (also available as `/api/eligibility`)
- `POST /api/assistant`
- `POST /api/crop-recommendation`

The crop predictor needs numeric `N`, `P`, `K`, `temperature`, `humidity`, `ph` and `rainfall` values. Its result is a model-based suggestion, not agronomic advice.

## Tests

```powershell
python -m unittest discover -s backend/tests -v
```