"""Boundary tests for real capture contracts. These do NOT test inference fidelity.

The end-to-end test must use a REAL, legally usable human exercise video.
"""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from ems.jobs import register_source
from ems.pose import _landmarks, _parse_detection, capture_registered_video
from ems.rights import InputValidationError


def fake_landmarks():
    # Unit-only fixture; NEVER passed as evidence of human pose detection.
    return [
        SimpleNamespace(x=i / 100, y=.25, z=-.05, visibility=.9, presence=.8)
        for i in range(33)
    ]


class PoseBoundaryTests(unittest.TestCase):
    def test_landmark_contract_has_33_points_and_confidence(self):
        raw = _landmarks(fake_landmarks())
        self.assertEqual(len(raw), 33)
        self.assertEqual(raw[0]["visibility"], .9)
        self.assertEqual(raw[32]["presence"], .8)

    def test_nan_landmark_rejected(self):
        points = fake_landmarks()
        points[20].z = float("nan")
        with self.assertRaisesRegex(InputValidationError, "nonfinite"):
            _landmarks(points)

    def test_ambiguous_subject_never_selects_arbitrary_person(self):
        pts = fake_landmarks()
        result = SimpleNamespace(pose_landmarks=[pts, pts],
                                 pose_world_landmarks=[pts, pts])
        obs = _parse_detection(result, 125)
        self.assertEqual(obs["state"], "AMBIGUOUS")
        self.assertNotIn("world_landmarks", obs)

    def test_missing_subject_is_explicit(self):
        result = SimpleNamespace(pose_landmarks=[], pose_world_landmarks=[])
        self.assertEqual(_parse_detection(result, 250),
                         {"timestamp_ms": 250, "state": "MISSING"})

    def test_detected_image_and_world_are_not_conflated(self):
        pts = fake_landmarks()
        world = fake_landmarks()
        world[0].z = .1234
        obs = _parse_detection(
            SimpleNamespace(pose_landmarks=[pts], pose_world_landmarks=[world]), 0
        )
        self.assertEqual(obs["state"], "DETECTED")
        self.assertNotEqual(obs["image_landmarks"][0]["z"],
                            obs["world_landmarks"][0]["z"])
        self.assertEqual(obs["confidence_core"], .9)

    def test_count_mismatch_rejected(self):
        pts = fake_landmarks()
        with self.assertRaisesRegex(InputValidationError, "count mismatch"):
            _parse_detection(SimpleNamespace(pose_landmarks=[pts],
                                                pose_world_landmarks=[]), 0)

    def test_requires_probed_registered_source_before_model_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            src = root / "sample.mp4"
            src.write_bytes(b"fake container for boundary tests only")
            registered = register_source(
                source=src, exercise_id="T01", rights_basis="owned",
                rights_evidence="Local boundary test only",
                jobs_dir=root / "jobs",
            )
            fake_model = root / "pose.task"
            fake_model.write_bytes(b"model-not-real")
            model_sha = hashlib.sha256(fake_model.read_bytes()).hexdigest()
            with self.assertRaisesRegex(InputValidationError, "media probe required"):
                capture_registered_video(
                    registered["job_id"], fake_model, model_sha, root / "jobs"
                )
            self.assertFalse((root / "jobs" / registered["job_id"] /
                              "pose_raw.json").exists())

    def test_model_hash_mismatch_blocks_before_loading_mediapipe(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "sample.mp4"
            source.write_bytes(b"input-only")
            job = register_source(source, "T01", "owned", "unit fixture", root / "jobs")
            manifest_path = root / "jobs" / job["job_id"] / "manifest.json"
            state = json.loads(manifest_path.read_text(encoding="utf-8"))
            state["media_probe"] = {"validation": "FULL_STREAM_DECODED",
                                    "source_sha256": state["source"]["sha256"],
                                    "duration_seconds": 1}
            manifest_path.write_text(json.dumps(state), encoding="utf-8")
            model = root / "pose.task"
            model.write_bytes(b"invalid model")
            with self.assertRaisesRegex(InputValidationError, "model SHA-256 mismatch"):
                capture_registered_video(
                    job["job_id"], model, "0" * 64, root / "jobs"
                )

    def test_rejects_invalid_sampling_resolution_or_digest(self):
        with self.assertRaises(InputValidationError):
            capture_registered_video("0" * 24, "none", "wrong")
        with self.assertRaisesRegex(InputValidationError, "sample-fps"):
            capture_registered_video("0" * 24, "none", "0" * 64, sample_fps=1)
        with self.assertRaisesRegex(InputValidationError, "resolution"):
            capture_registered_video("0" * 24, "none", "0" * 64, resolution=255)


if __name__ == "__main__":
    unittest.main()
