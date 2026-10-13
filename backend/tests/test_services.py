import unittest

from backend.api.schemes import list_schemes
from backend.models.farmer import ProfileError, normalize_profile
from backend.services.ai import answer_farmer
from backend.services.eligibility import match_schemes
from backend.services.recommendation import recommend_crop


class FarmerProfileTests(unittest.TestCase):
    def test_normalizes_optional_values(self):
        profile = normalize_profile({"state": " Tamil Nadu ", "land_area_acres": "2"})
        self.assertEqual(profile["state"], "Tamil Nadu")
        self.assertEqual(profile["land_area_acres"], 2)
        self.assertEqual(profile["ownership"], "unknown")

    def test_rejects_invalid_land_area(self):
        with self.assertRaises(ProfileError):
            normalize_profile({"land_area_acres": "-1"})

    def test_rejects_non_object_profile(self):
        with self.assertRaises(ProfileError):
            normalize_profile([])


class SchemeMatchingTests(unittest.TestCase):
    def test_seed_entries_are_never_presented_as_verified_eligibility(self):
        catalog = list_schemes()
        self.assertGreaterEqual(len(catalog), 4)
        self.assertTrue(all(scheme["verification_status"] == "unverified" for scheme in catalog))

        result = match_schemes({"state": "Tamil Nadu", "need": "crop-insurance"})
        self.assertTrue(result["matches"])
        self.assertTrue(all(item["eligibility"] == "needs_review" for item in result["matches"]))
        self.assertIn("not an official eligibility decision", result["disclaimer"])

    def test_category_filter_only_returns_relevant_catalog_leads(self):
        result = match_schemes({"need": "crop-insurance"})
        self.assertEqual(
            [item["scheme"]["id"] for item in result["matches"]],
            ["pmfby"],
        )

    def test_no_requirement_claim_without_verified_checklist(self):
        result = match_schemes({"need": "income-support"})
        match = next(item for item in result["matches"] if item["scheme"]["id"] == "pm-kisan")
        self.assertEqual(match["missing_documents"], [])
        self.assertIn("has not been verified", match["documents_note"])

    def test_assistant_detects_tanglish_crop_and_acreage(self):
        result = answer_farmer("Enakku 2 acre land irukku, paddy poduren. Enna support?", language="tanglish")
        self.assertEqual(result["detected_profile"]["land_area_acres"], 2)
        self.assertEqual(result["detected_profile"]["crop"], "rice")
        self.assertIn("Unga details", result["answer"])

    def test_crop_detection_does_not_match_substrings(self):
        result = answer_farmer("What price support is available?", language="en")
        self.assertEqual(result["detected_profile"]["crop"], "")

    def test_rejects_empty_assistant_question(self):
        with self.assertRaises(ValueError):
            answer_farmer("")

    def test_assistant_rejects_malformed_profile_and_language(self):
        with self.assertRaises(ValueError):
            answer_farmer("scheme help", profile_payload=[])
        with self.assertRaises(ValueError):
            answer_farmer("scheme help", language="fr")


class CropRecommendationTests(unittest.TestCase):
    def test_trained_model_returns_crop_and_confidence(self):
        result = recommend_crop(
            {
                "N": 90,
                "P": 42,
                "K": 43,
                "temperature": 20.87974371,
                "humidity": 82.00274423,
                "ph": 6.502985292000001,
                "rainfall": 202.9355362,
            }
        )
        self.assertEqual(result["recommendation"], "rice")
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)
        self.assertLessEqual(len(result["alternatives"]), 3)
        self.assertIn("Trained crop recommendation classifier", result["method"])

    def test_rejects_missing_crop_features(self):
        with self.assertRaises(ValueError):
            recommend_crop({"N": 10})

    def test_rejects_non_finite_crop_features(self):
        with self.assertRaises(ValueError):
            recommend_crop(
                {
                    "N": float("nan"),
                    "P": 42,
                    "K": 43,
                    "temperature": 20.8,
                    "humidity": 82,
                    "ph": 6.5,
                    "rainfall": 203,
                }
            )


if __name__ == "__main__":
    unittest.main()
