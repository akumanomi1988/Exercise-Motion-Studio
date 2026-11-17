"""AG0 manifest-only tests; bytes below are NOT real Blender/GLB assets."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ems.catalog import inspect_asset_folder, scan_asset_catalog
from ems.rights import InputValidationError


class CatalogManifestTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.asset = self.root / "asset"
        self.asset.mkdir()
        self.files = {
            "asset.blend": b"test-blend-placeholder" * 200,
            "asset.glb": b"test-glb-placeholder" * 200,
            "preview.png": b"test-png-placeholder" * 200,
        }
        for name, data in self.files.items():
            (self.asset / name).write_bytes(data)
        self.meta = {
            "schema_version": "1.0", "asset_id": "ems.equipment.dumbbell.hex.10kg",
            "version": "0.1.0", "category": "free_weight", "unit": "meter",
            "dimensions_m": {"length_x": .47, "width_y": .17, "height_z": .17},
            "source": {"kind": "ORIGINAL_PROCEDURAL"},
            "licenses": {"status": "PENDING", "distribution_approved": False,
                         "reviewer": None},
            "models": {"editable": "asset.blend", "distribution": "asset.glb",
                       "thumbnail": "preview.png"},
            "grip_points": [{"id": "main", "position_m": [0, 0, 0],
                             "axis": [1, 0, 0]}],
            "attachment_points": [{"id": "head", "position_m": [.15, 0, 0]}],
            "collision_shapes": [{"shape": "cylinder", "center_m": [0, 0, 0],
                                  "axis": [1, 0, 0], "radius_m": .08, "length_m": .4}],
            "contact_surfaces": [{"id": "front", "point_m": [.2, 0, 0],
                                  "normal": [1, 0, 0]}],
            "file_sha256": {name: hashlib.sha256(data).hexdigest()
                            for name, data in self.files.items()},
        }
        self.save()

    def save(self):
        (self.asset / "asset.json").write_text(json.dumps(self.meta), encoding="utf-8")

    def test_manifest_integrity_does_not_claim_real_geometry_or_approval(self):
        outcome = inspect_asset_folder(self.asset)
        self.assertEqual(outcome["status"], "MANIFEST_INTEGRITY_PASS")
        self.assertFalse(outcome["commercial_distribution_allowed"])
        self.assertEqual(outcome["external_geometry_validation"], "NOT_PERFORMED")

    def test_unreviewed_asset_cannot_be_marked_commercial(self):
        with self.assertRaisesRegex(InputValidationError, "rights review incomplete"):
            inspect_asset_folder(self.asset, require_commercial=True)

    def test_rejects_modified_glb_hash(self):
        (self.asset / "asset.glb").write_bytes(b"modified" * 400)
        with self.assertRaisesRegex(InputValidationError, "SHA-256 mismatch"):
            inspect_asset_folder(self.asset)

    def test_rejects_unsafe_model_path(self):
        self.meta["models"]["distribution"] = "../asset.glb"
        self.save()
        with self.assertRaisesRegex(InputValidationError, "unsafe distribution"):
            inspect_asset_folder(self.asset)

    def test_rejects_nonfinite_collision_dimensions(self):
        self.meta["collision_shapes"][0]["radius_m"] = float("nan")
        self.save()
        with self.assertRaisesRegex(InputValidationError, "radius_m"):
            inspect_asset_folder(self.asset)

    def test_rejects_nonunit_grip_axis(self):
        self.meta["grip_points"][0]["axis"] = [3, 0, 0]
        self.save()
        with self.assertRaisesRegex(InputValidationError, "unit vector"):
            inspect_asset_folder(self.asset)

    def test_duplicate_catalog_id_fails(self):
        other = self.root / "other"
        other.mkdir()
        for name, data in self.files.items():
            (other / name).write_bytes(data)
        (other / "asset.json").write_text(json.dumps(self.meta), encoding="utf-8")
        with self.assertRaisesRegex(InputValidationError, "duplicate ID"):
            scan_asset_catalog(self.root)

    def test_approved_state_without_review_evidence_is_blocked(self):
        self.meta["licenses"]["status"] = "APPROVED"
        self.meta["licenses"]["distribution_approved"] = True
        self.save()
        with self.assertRaisesRegex(InputValidationError, "rights review incomplete"):
            inspect_asset_folder(self.asset, require_commercial=True)


if __name__ == "__main__":
    unittest.main()
