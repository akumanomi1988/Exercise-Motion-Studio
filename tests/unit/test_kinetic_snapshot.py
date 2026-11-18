"""Pure contract fixtures only. Real 908-entry Kinetic audit runs in G5 CI."""
import json
import tempfile
import unittest
from pathlib import Path

from ems.kinetic import build_index, read_pinned, COMMIT
from ems.rights import InputValidationError


class KineticMetadataContractTests(unittest.TestCase):
    def setUp(self):
        self.bar = "00000000-0000-4000-8000-000000000001"
        self.band = "00000000-0000-4000-8000-000000000002"
        self.exid = "00000000-0000-4000-8000-000000000003"
        self.equipment = [
            {"id": self.bar, "name": "Barra", "family": "barbell"},
            {"id": self.band, "name": "Banda", "family": "bands"},
        ]
        self.exercises = [{
            "id": self.exid, "name": "Press de banca",
            "slug": "barbell-bench-press", "category": "strength",
            "equipment": [{"id": self.bar, "numItems": 1}],
            "youtube": {
                "url": "https://youtube.example/watch",
                "thumbnailUrl": "https://youtube.example/hqdefault.jpg",
            },
            "instructions": ["No incorporar instrucciones audiovisuales"],
        }]

    def test_preserves_ids_while_dropping_external_media(self):
        report = build_index(self.exercises, self.equipment)
        self.assertEqual(report["exercise_count"], 1)
        self.assertEqual(report["equipment_type_count"], 2)
        self.assertEqual(report["equipment_association_count"], 1)
        self.assertEqual(report["unmapped_equipment_types"], 2)
        self.assertEqual(report["approved_exercises"], 0)
        self.assertEqual(report["source"]["commit"], COMMIT)
        self.assertEqual(report["exercises"][0]["kinetic_exercise_id"], self.exid)
        self.assertEqual(report["exercises"][0]["equipment_ids"], [self.bar])
        serialized = json.dumps(report).lower()
        self.assertNotIn("youtube.example", serialized)
        self.assertNotIn("thumbnailurl", serialized)
        self.assertNotIn("repdb", serialized.replace(
            '"repdb_imported": false', ""))

    def test_unknown_equipment_does_not_get_invented(self):
        self.exercises[0]["equipment"][0]["id"] = (
            "00000000-0000-4000-8000-0000000000ff"
        )
        with self.assertRaisesRegex(InputValidationError, "nonexistent"):
            build_index(self.exercises, self.equipment)

    def test_duplicate_exercise_id_is_rejected(self):
        self.exercises.append(dict(self.exercises[0], slug="another-exercise"))
        with self.assertRaisesRegex(InputValidationError, "duplicate exercise UUID"):
            build_index(self.exercises, self.equipment)

    def test_duplicate_equipment_link_is_rejected(self):
        self.exercises[0]["equipment"].append({"id": self.bar})
        with self.assertRaisesRegex(InputValidationError, "duplicate equipment link"):
            build_index(self.exercises, self.equipment)

    def test_unpinned_input_cannot_be_audited(self):
        with tempfile.TemporaryDirectory() as root:
            f = Path(root) / "exercises.json"
            f.write_text(json.dumps(self.exercises), encoding="utf-8")
            with self.assertRaisesRegex(InputValidationError, "blob mismatch"):
                read_pinned(f, "es/exercises.json")

    def test_missing_slug_is_rejected(self):
        self.exercises[0]["slug"] = None
        with self.assertRaisesRegex(InputValidationError, "slug"):
            build_index(self.exercises, self.equipment)


if __name__ == "__main__":
    unittest.main()
