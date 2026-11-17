"""Isolated invariants for intermediate skeleton solver, NOT real exercise E2E.

Hand-built coordinates in unit tests merely check solver algebra. Real source
validation runs separately in pose-ci.yml against licensed human footage.
"""

import copy
import math
import unittest

from ems.rights import InputValidationError
from ems.solver import SEGMENTS, _quaternion_between, normalize_pose_observations


def _frame(timestamp_ms, stretch=1.0):
    coords = [(0.0, 0.0, 0.0)] * 33
    anchors = {
        0: (0.0, -.81, .01),
        11: (-.19, -.49, 0.), 12: (.19, -.49, 0.),
        13: (-.39, -.31, -.04), 14: (.39, -.31, -.04),
        15: (-.45, -.07, -.06), 16: (.45, -.07, -.06),
        23: (-.11, 0., 0.), 24: (.11, 0., 0.),
        25: (-.13, .41, -.06), 26: (.13, .41, -.06),
        27: (-.15, .82, -.02), 28: (.15, .82, -.02),
        31: (-.15, .88, -.18), 32: (.15, .88, -.18),
    }
    for key, xyz in anchors.items():
        coords[key] = tuple(v * stretch for v in xyz)
    pts = [
        dict(x=x, y=y, z=z, visibility=.95, presence=.95)
        for x, y, z in coords
    ]
    return {"timestamp_ms": timestamp_ms, "state": "DETECTED",
            "world_landmarks": pts}


def raw():
    return {
        "method": "video_inference_real",
        "data_type": "MEDIAPIPE_RAW_POSE_OBSERVATIONS",
        "space": {"absolute_root_motion": False},
        "job_id": "a" * 24, "source_sha256": "1" * 64,
        "model": {"sha256": "2" * 64},
        "frames": [
            _frame(0), _frame(125, 1.04), _frame(250, .97), _frame(375, 1.02)
        ],
    }


class SkeletonAlgebraTests(unittest.TestCase):
    def test_lengths_locked_to_median_without_falsifying_raw_variation(self):
        data = normalize_pose_observations(raw())
        self.assertEqual(data["data_type"], "INTERMEDIATE_SKELETON_NOT_FINAL_MOTION")
        self.assertGreater(data["qa"]["max_raw_relative_segment_length_deviation"], .01)
        self.assertLess(data["qa"]["max_solved_relative_segment_length_deviation"], 1e-9)
        self.assertEqual(data["qa"]["length_1_percent_check"], "TECHNICAL_PASS")
        self.assertFalse(data["qa"]["commercial_approval"])
        self.assertEqual(len(data["parent_child_segments"]), len(SEGMENTS))

    def test_every_swing_quaternion_is_unit_length(self):
        solved = normalize_pose_observations(raw())
        for frame in solved["frames"]:
            for q in frame["local_swing_quaternions_xyzw"].values():
                self.assertAlmostEqual(math.sqrt(sum(x*x for x in q)), 1, places=7)

    def test_missing_person_not_synthetically_filled(self):
        document = raw()
        document["frames"][2] = {"timestamp_ms": 250, "state": "MISSING"}
        solved = normalize_pose_observations(document)
        self.assertEqual(solved["frames"][2], {"timestamp_ms": 250, "state": "MISSING"})
        self.assertEqual(solved["qa"]["status"], "REVIEW_REQUIRED")

    def test_low_visibility_is_flagged_not_silently_approved(self):
        doc = raw()
        doc["frames"][0]["world_landmarks"][15]["visibility"] = .01
        data = normalize_pose_observations(doc)
        self.assertGreater(data["qa"]["low_visibility_segment_samples"], 0)
        self.assertTrue(data["frames"][0]["unreliable_segments"])

    def test_invalid_real_inference_provenance_is_blocked(self):
        doc = raw()
        doc["method"] = "procedural_generated"
        with self.assertRaisesRegex(InputValidationError, "actual MediaPipe"):
            normalize_pose_observations(doc)

    def test_nonmonotonic_timestamps_are_blocked(self):
        doc = raw()
        doc["frames"][2]["timestamp_ms"] = 120
        with self.assertRaisesRegex(InputValidationError, "timestamps"):
            normalize_pose_observations(doc)

    def test_quaternion_antiparallel_is_finite_unit(self):
        q = _quaternion_between((1., 0., 0.), (-1., 0., 0.))
        self.assertAlmostEqual(math.sqrt(sum(v*v for v in q)), 1)
        self.assertAlmostEqual(q[3], 0)

    def test_no_absolute_root_motion_or_human_qa_claim(self):
        data = normalize_pose_observations(raw())
        self.assertEqual(data["qa"]["absolute_root_motion"], "NOT_SOLVED")
        self.assertEqual(data["qa"]["avatar_skinning"], "NOT_PRESENT")
        self.assertEqual(data["qa"]["human_visual_review"], "PENDING")


if __name__ == "__main__":
    unittest.main()
