"""Contract-only fixtures; real-video E2E is separately validated in CI.

No fixture created here proves MoCap or human appearance. The CLI integration
must also be exercised against real SHA-identified Blender/MediaPipe outputs.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ems.review_queue import compile_real_video_review, write_real_video_review
from ems.rights import InputValidationError


class ReviewQueueContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ems-review-unit-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.solved = self.root / "solved_skeleton.json"
        self.male = self.root / "male"
        self.female = self.root / "female"
        self.male.mkdir()
        self.female.mkdir()
        self.raw = {
            "data_type": "INTERMEDIATE_SKELETON_NOT_FINAL_MOTION",
            "method": "MEDIAPIPE_HIP_RELATIVE_GEOMETRIC_CONSTRAINTS",
            "source_sha256": "a" * 64, "model_sha256": "b" * 64,
            "frames": [
                {"timestamp_ms": 0, "state": "SOLVED_REVIEW_REQUIRED"},
                {"timestamp_ms": 200, "state": "SOLVED_REVIEW_REQUIRED"},
                {"timestamp_ms": 400, "state": "SOLVED_REVIEW_REQUIRED"},
            ],
            "qa": {
                "commercial_approval": False,
                "low_visibility_segment_samples": 2,
                "temporal_review_events": [{
                    "timestamp_ms": 200, "segment": "leftKnee",
                    "angular_speed_deg_per_s": 481.1,
                }],
            },
        }
        self.save(self.solved, self.raw)
        for variant, folder in (("male", self.male), ("female", self.female)):
            self.save(folder / "retarget_manifest.json", {
                "data_type": "SKINNED_HUMAN_RETARGET_DIAGNOSTIC_NOT_FINAL_MOTION",
                "variant": variant, "solved_skeleton_sha256": self.hash(self.solved),
                "original_video_sha256": "a" * 64, "pose_model_sha256": "b" * 64,
                "source_frames": 3, "sample_fps": 6,
                "source_video_license": "CC-BY-SA-4.0",
                "commercial_approval": False, "human_visual_review": "PENDING",
                "file_sha256": {"retarget_review.glb": "c" * 64},
                "full_body_ik": "NOT_IMPLEMENTED",
                "foot_contacts": "NOT_SOLVED", "hand_grips": "NOT_SOLVED",
                "rights_review": "PENDING",
            })
            self.save(folder / "retarget_qa.json", {
                "variant": variant, "source_frames": 3,
                "commercial_approval": False,
                "human_visual_review": "PENDING",
                "joint_attachment": {"status": "TECHNICAL_PASS"},
                "technical_skinned_retarget": "PASS",
                "kinematic_fidelity": {
                    "status": "FAIL_REVIEW_REQUIRED",
                    "screening_limit_degrees": 15.0,
                    "review_event_count": 1,
                    "review_events_first_25": [{
                        "timestamp_ms": 200,
                        "joint": "leftKnee",
                        "source_flexion_degrees": 55.0,
                        "glb_flexion_degrees": 78.5,
                        "error_degrees": 23.5,
                    }],
                },
            })

    @staticmethod
    def save(path, data):
        path.write_text(json.dumps(data), encoding="utf-8")

    @staticmethod
    def hash(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def inspect(self):
        return compile_real_video_review(self.male, self.female, self.solved)

    def test_review_only_and_both_variant_alerts(self):
        queue = self.inspect()
        self.assertEqual(queue["status"], "REVIEW_REQUIRED")
        self.assertEqual(queue["release_gate"], "BLOCKED")
        self.assertFalse(queue["approved"])
        self.assertEqual(queue["exercises_approved"], 0)
        self.assertEqual(queue["source_video_license"], "CC-BY-SA-4.0")
        events = [item for item in queue["issues"]
                  if item["kind"] == "JOINT_FLEXION_FIDELITY"]
        self.assertEqual({e["variant"] for e in events}, {"male", "female"})
        self.assertEqual([e["detail"]["source_frame"] for e in events], [2, 2])
        self.assertEqual(len([e for e in queue["issues"]
                              if e["kind"] == "SOURCE_ANGULAR_OUTLIER"]), 1)
        self.assertEqual(len([e for e in queue["issues"]
                              if e["kind"] == "SOURCE_LOW_VISIBILITY"]), 1)
        self.assertEqual(queue["issue_count"], len(queue["issues"]))

    def test_idempotent_output_and_no_overwrite_of_changed_evidence(self):
        target = self.root / "queue.json"
        result = write_real_video_review(self.male, self.female,
                                         self.solved, target)
        self.assertEqual(result["release_gate"], "BLOCKED")
        original = target.read_bytes()
        write_real_video_review(self.male, self.female, self.solved, target)
        self.assertEqual(original, target.read_bytes())
        target.write_text("not the same data", encoding="utf-8")
        with self.assertRaisesRegex(InputValidationError, "differs"):
            write_real_video_review(self.male, self.female, self.solved, target)

    def test_mismatched_video_provenance_is_refused(self):
        file = self.female / "retarget_manifest.json"
        manifest = json.loads(file.read_text())
        manifest["original_video_sha256"] = "f" * 64
        self.save(file, manifest)
        with self.assertRaisesRegex(InputValidationError, "provenance mismatch"):
            self.inspect()

    def test_missing_measured_event_never_becomes_pass(self):
        file = self.male / "retarget_qa.json"
        qa = json.loads(file.read_text())
        qa["kinematic_fidelity"]["review_events_first_25"] = []
        self.save(file, qa)
        with self.assertRaisesRegex(InputValidationError, "no source evidence"):
            self.inspect()

    def test_truncated_review_events_explicitly_block(self):
        file = self.male / "retarget_qa.json"
        qa = json.loads(file.read_text())
        qa["kinematic_fidelity"]["review_event_count"] = 3
        self.save(file, qa)
        queue = self.inspect()
        self.assertTrue(any(x["kind"] == "EVENTS_TRUNCATED"
                            for x in queue["issues"]))
        self.assertEqual(queue["release_gate"], "BLOCKED")

    def test_unreliable_synthetic_approval_claim_rejected(self):
        file = self.male / "retarget_manifest.json"
        manifest = json.loads(file.read_text())
        manifest["commercial_approval"] = True
        self.save(file, manifest)
        with self.assertRaisesRegex(InputValidationError, "commercial rights"):
            self.inspect()


if __name__ == "__main__":
    unittest.main()
