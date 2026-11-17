"""I1 P-04 intermediate skeleton with invariant segment lengths.

All directions originate from REAL, SHA-verified MediaPipe 3D observations.
The solver enforces per-segment lengths and estimates *swing-only* rotations.
It CANNOT determine bone twist, calibrated world root motion, contact, IK,
body/equipment collision or a human avatar's deformable skinning. It produces
solved_skeleton.json, NOT approved motion.json, GLB or commercial media.
"""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any

from ems.jobs import sha256_file
from ems.pose import _JOB_ID, _require, _write_atomic
from ems.rights import InputValidationError

# Directed canonical topological order (parent node, child node).
# Midpoint nodes are mathematical anatomical anchors, NOT MediaPipe joints.
SEGMENTS = (
    ("pelvis", "leftHip"), ("pelvis", "rightHip"),
    ("pelvis", "chest"), ("chest", "leftShoulder"),
    ("chest", "rightShoulder"), ("chest", "nose"),
    ("leftShoulder", "leftElbow"), ("leftElbow", "leftWrist"),
    ("rightShoulder", "rightElbow"), ("rightElbow", "rightWrist"),
    ("leftHip", "leftKnee"), ("leftKnee", "leftAnkle"),
    ("leftAnkle", "leftToe"), ("rightHip", "rightKnee"),
    ("rightKnee", "rightAnkle"), ("rightAnkle", "rightToe"),
)
NODES = {
    "nose": 0, "leftShoulder": 11, "rightShoulder": 12,
    "leftElbow": 13, "rightElbow": 14,
    "leftWrist": 15, "rightWrist": 16,
    "leftHip": 23, "rightHip": 24,
    "leftKnee": 25, "rightKnee": 26,
    "leftAnkle": 27, "rightAnkle": 28,
    "leftToe": 31, "rightToe": 32,
}
ROOT = "pelvis"


def _add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _scale(a, k):
    return tuple(x * k for x in a)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _norm(a):
    return math.sqrt(_dot(a, a))


def _unit(a):
    mag = _norm(a)
    if not math.isfinite(mag) or mag < 1e-7:
        raise InputValidationError("degenerate joint direction")
    return _scale(a, 1.0 / mag)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _quaternion_between(a, b):
    """Shortest swing-only quaternion XYZW. Twist is NOT observable."""
    a, b = _unit(a), _unit(b)
    dot = max(-1.0, min(1.0, _dot(a, b)))
    if dot > 1.0 - 1e-8:
        return (0.0, 0.0, 0.0, 1.0)
    if dot < -1.0 + 1e-8:
        trial = (1., 0., 0.) if abs(a[0]) < .9 else (0., 1., 0.)
        axis = _unit(_cross(a, trial))
        return (*axis, 0.0)
    xyz = _cross(a, b)
    q = (*xyz, 1.0 + dot)
    mag = math.sqrt(sum(v * v for v in q))
    return tuple(v / mag for v in q)


def _qmul(q, r):
    x1, y1, z1, w1 = q
    x2, y2, z2, w2 = r
    return (
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
    )


def _qconj(q):
    return (-q[0], -q[1], -q[2], q[3])


def _landmark_position(point):
    # MediaPipe world landmarks, not metric-calibrated scene coordinates.
    xyz = tuple(float(point[axis]) for axis in ("x", "y", "z"))
    if not all(math.isfinite(v) for v in xyz):
        raise InputValidationError("nonfinite MediaPipe 3D joint")
    # This is a documented diagnostic coordinate conversion, not a validated
    # anatomical rest alignment or global coordinate solve.
    return (xyz[0], -xyz[1], -xyz[2])


def _observed(frame):
    pts = frame["world_landmarks"]
    if len(pts) != 33:
        raise InputValidationError("expected 33 world landmarks per detected frame")
    p = {name: _landmark_position(pts[index]) for name, index in NODES.items()}
    p["pelvis"] = _scale(_add(p["leftHip"], p["rightHip"]), .5)
    p["chest"] = _scale(_add(p["leftShoulder"], p["rightShoulder"]), .5)
    # Store positions relative to pelvic midpoint; this removes all absolute
    # locomotion, which a single monocular camera does not determine.
    root = p["pelvis"]
    positions = {name: _sub(point, root) for name, point in p.items()}
    confidence = {}
    for name, idx in NODES.items():
        raw = pts[idx].get("visibility")
        confidence[name] = float(raw) if raw is not None else 0.0
    confidence["pelvis"] = min(confidence["leftHip"], confidence["rightHip"])
    confidence["chest"] = min(confidence["leftShoulder"], confidence["rightShoulder"])
    return positions, confidence


def normalize_pose_observations(raw: dict[str, Any]) -> dict[str, Any]:
    """Build a topologically linked, fixed-length intermediate skeleton.

    Exact fixed lengths are enforced by geometry, not by modifying test
    thresholds. Estimation uncertainty is not removed, only made explicit.
    """
    _require(raw.get("method") == "video_inference_real"
             and raw.get("data_type") == "MEDIAPIPE_RAW_POSE_OBSERVATIONS",
             "solver requires actual MediaPipe inference observations")
    _require(raw.get("space", {}).get("absolute_root_motion") is False,
             "unknown global-motion convention")
    frames = raw.get("frames", [])
    _require(isinstance(frames, list) and len(frames) >= 2,
             "solver needs at least two time samples")
    times = [f["timestamp_ms"] for f in frames]
    _require(all(isinstance(t, int) and t >= 0 for t in times)
             and all(b > a for a, b in zip(times, times[1:])),
             "timestamps must be strictly increasing milliseconds")
    detected = [f for f in frames if f["state"] == "DETECTED"]
    _require(len(detected) >= 3, "at least three real detections needed")
    observations = [_observed(f) for f in detected]
    min_visibility = 0.5

    # Determine each segment's consistent nominal length from high-visibility
    # frames; do NOT backfill undetected segments with unflagged estimates.
    lengths, rest_directions = {}, {}
    raw_max_variation = {}
    for parent, child in SEGMENTS:
        measured = []
        all_lengths = []
        directions = []
        for pos, conf in observations:
            delta = _sub(pos[child], pos[parent])
            mag = _norm(delta)
            _require(math.isfinite(mag) and mag > 1e-6,
                     f"degenerate segment {parent}->{child}")
            all_lengths.append(mag)
            if min(conf[parent], conf[child]) >= min_visibility:
                measured.append(mag)
                directions.append(_unit(delta))
        _require(len(measured) >= 3,
                 f"insufficient visible samples to calibrate {child}")
        median = statistics.median(measured)
        _require(math.isfinite(median) and 0.015 < median < 1.5,
                 f"unreasonable segment length for {child}: {median}")
        lengths[child] = median
        rest_directions[child] = directions[0]
        raw_max_variation[child] = max(abs(d - median) / median for d in all_lengths)

    normalized = []
    maximum_step_degrees = 0.0
    prior_dirs = {}
    unreliable = 0
    solved_lengths_max_error = 0.0
    for frame in frames:
        timestamp = frame["timestamp_ms"]
        if frame["state"] != "DETECTED":
            normalized.append({"timestamp_ms": timestamp, "state": frame["state"]})
            continue
        observed, confidence = _observed(frame)
        positions = {ROOT: (0., 0., 0.)}
        global_rot = {ROOT: (0., 0., 0., 1.)}
        local_rot = {}
        flags = []
        for parent, child in SEGMENTS:
            direction = _unit(_sub(observed[child], observed[parent]))
            if min(confidence[parent], confidence[child]) < min_visibility:
                unreliable += 1
                flags.append({"segment": child, "reason": "LOW_VISIBILITY"})
            # Never invent a 3D angle: observed direction is retained, and low
            # quality remains explicitly marked for human review.
            if child in prior_dirs:
                angle = math.degrees(math.acos(max(
                    -1., min(1., _dot(prior_dirs[child], direction))
                )))
                maximum_step_degrees = max(maximum_step_degrees, angle)
            prior_dirs[child] = direction
            target = _add(positions[parent], _scale(direction, lengths[child]))
            positions[child] = target
            solved_len = _norm(_sub(target, positions[parent]))
            solved_lengths_max_error = max(
                solved_lengths_max_error, abs(solved_len - lengths[child]) / lengths[child]
            )
            # Swing-only approximation. Without torsion/IK this quaternion
            # cannot be used as final avatar bone rotation.
            absolute = _quaternion_between(rest_directions[child], direction)
            global_rot[child] = absolute
            local_rot[child] = _qmul(_qconj(global_rot[parent]), absolute)
        normalized.append({
            "timestamp_ms": timestamp,
            "state": "SOLVED_REVIEW_REQUIRED",
            "root_position": [0., 0., 0.],
            "joints": {k: [round(v, 9) for v in pos] for k, pos in positions.items()},
            "local_swing_quaternions_xyzw": {
                k: [round(c, 9) for c in quat] for k, quat in local_rot.items()
            },
            "unreliable_segments": flags,
        })

    qa = {
        "status": "REVIEW_REQUIRED",
        "bone_length_reference": "MEDIAN_HIGH_VISIBILITY_WORLD_ESTIMATE",
        "max_raw_relative_segment_length_deviation": round(max(raw_max_variation.values()), 6),
        "max_solved_relative_segment_length_deviation": round(solved_lengths_max_error, 12),
        "max_interframe_swing_degrees": round(maximum_step_degrees, 6),
        "low_visibility_segment_samples": unreliable,
        "length_1_percent_check": "TECHNICAL_PASS"
            if solved_lengths_max_error <= 0.01 else "FAIL",
        "absolute_root_motion": "NOT_SOLVED",
        "bone_twist": "NOT_OBSERVABLE",
        "contacts_and_ik": "NOT_SOLVED",
        "avatar_skinning": "NOT_PRESENT",
        "human_visual_review": "PENDING",
        "commercial_approval": False,
    }
    return {
        "schema_version": "0.1.0",
        "data_type": "INTERMEDIATE_SKELETON_NOT_FINAL_MOTION",
        "method": "MEDIAPIPE_HIP_RELATIVE_GEOMETRIC_CONSTRAINTS",
        "job_id": raw["job_id"],
        "source_sha256": raw["source_sha256"],
        "model_sha256": raw["model"]["sha256"],
        "coordinate_system": "APPROX_RH_Y_UP_RELATIVE_UNCALIBRATED",
        "skeleton_profile_id": "ems.humanoid.intermediate.v1",
        "root_name": ROOT,
        "parent_child_segments": [
            {"parent": parent, "child": child, "nominal_length_m": round(lengths[child], 9)}
            for parent, child in SEGMENTS
        ],
        "frames": normalized,
        "qa": qa,
    }


def solve_registered_capture(job_id: str, jobs_dir: str | Path = "data/jobs"):
    _require(bool(_JOB_ID.fullmatch(job_id)), "invalid job ID")
    folder = Path(jobs_dir).expanduser().resolve() / job_id
    manifest_file = folder / "manifest.json"
    _require(manifest_file.is_file() and not manifest_file.is_symlink(),
             "registered manifest missing")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    _require(manifest.get("job_id") == job_id, "job identity mismatch")
    capture = manifest.get("pose_capture", {})
    _require(capture.get("artifact") == "pose_raw.json",
             "verified raw capture required before skeleton solving")
    path = folder / "pose_raw.json"
    _require(path.is_file() and not path.is_symlink(), "raw pose missing or unsafe")
    _require(sha256_file(path) == capture.get("sha256"),
             "pose observations changed since capture")
    raw = json.loads(path.read_text(encoding="utf-8"))
    _require(raw.get("job_id") == job_id, "raw pose job identity mismatch")
    _require(raw.get("source_sha256") == manifest["source"]["sha256"],
             "raw pose source integrity mismatch")
    result = normalize_pose_observations(raw)
    out = folder / "solved_skeleton.json"
    _write_atomic(out, result)
    digest = sha256_file(out)
    manifest["solved_skeleton"] = {
        "artifact": "solved_skeleton.json", "sha256": digest,
        "status": "REVIEW_REQUIRED",
    }
    manifest.setdefault("pipeline", {})["skeleton"] = "REVIEW_REQUIRED"
    _write_atomic(manifest_file, manifest)
    return {
        "job_id": job_id, "status": "INTERMEDIATE_SKELETON_REVIEW_REQUIRED",
        "artifact": "solved_skeleton.json", "sha256": digest,
        "qa": result["qa"], "commercial_approval": False,
    }
