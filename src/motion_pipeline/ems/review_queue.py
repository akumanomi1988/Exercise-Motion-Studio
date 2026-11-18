"""Deterministic, fail-closed review queue from REAL-video dual-avatar QA.

Input must be existing, hash-linked solved_skeleton.json and male/female
Blender E2E diagnostic reports. This does not approve or repair motion,
identify a human reviewer, or lift any CC BY-SA/other rights restrictions.
No source video/image bytes are copied into the queue.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from ems.rights import InputValidationError

_HEX = re.compile(r"^[a-f0-9]{64}$")
_VARIANTS = ("male", "female")


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise InputValidationError("review queue: " + reason)


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _read(path: Path) -> dict[str, Any]:
    _require(path.is_file() and not path.is_symlink(), "missing/unsafe " + path.name)
    _require(path.stat().st_size <= 2 * 1024 * 1024, "input exceeds 2MiB")
    try:
        result = json.loads(path.read_text(encoding="utf-8"),
                            parse_constant=lambda _: _require(False, "nonfinite JSON"))
    except (ValueError, UnicodeError) as exc:
        raise InputValidationError("review queue: invalid UTF-8 JSON " + path.name) from exc
    _require(isinstance(result, dict), "JSON object required " + path.name)
    return result


def _sha(value: object, label: str) -> str:
    _require(isinstance(value, str) and bool(_HEX.fullmatch(value)),
             "invalid SHA-256 " + label)
    return value


def _number(value: object, label: str, lower: float = 0.0) -> float:
    _require(type(value) in (int, float) and math.isfinite(value) and value >= lower,
             "invalid number " + label)
    return float(value)


def _issue(source: str, variant: str | None, kind: str, marker: str,
           detail: dict[str, Any]) -> dict[str, Any]:
    key = json.dumps([source, variant, kind, marker],
                     separators=(",", ":"), ensure_ascii=True)
    return {"id": hashlib.sha256(key.encode("utf-8")).hexdigest()[:24],
            "severity": "BLOCKING", "variant": variant, "kind": kind,
            "marker": marker, "detail": detail,
            "review_state": "REVIEW_REQUIRED"}


def compile_real_video_review(male_dir: str | Path, female_dir: str | Path,
                              solved_path: str | Path) -> dict[str, Any]:
    """Produce a versioned review queue; incompatible data always aborts."""
    roots = {
        "male": Path(male_dir).expanduser().resolve(strict=True),
        "female": Path(female_dir).expanduser().resolve(strict=True),
    }
    _require(all(root.is_dir() for root in roots.values()),
             "avatar input must be directories")
    _require(roots["male"] != roots["female"], "distinct variant directories required")
    solved_file = Path(solved_path).expanduser().resolve(strict=True)
    # resolve(strict=True) removes symlink path identity: reject symlinks
    # separately at the API boundary before read below.
    solved = _read(solved_file)
    solved_digest = _hash(solved_file)
    _require(solved.get("data_type") == "INTERMEDIATE_SKELETON_NOT_FINAL_MOTION",
             "source must be an actual intermediate skeleton")
    _require(solved.get("method") == "MEDIAPIPE_HIP_RELATIVE_GEOMETRIC_CONSTRAINTS",
             "unsupported generated/procedural motion source")
    _require(solved.get("qa", {}).get("commercial_approval") is False,
             "input skeleton cannot be commercially approved")
    source = _sha(solved.get("source_sha256"), "video")
    model = _sha(solved.get("model_sha256"), "model")
    frames = solved.get("frames")
    _require(isinstance(frames, list) and len(frames) >= 3,
             "actual source frames missing")
    first_ms = frames[0].get("timestamp_ms")
    _require(type(first_ms) is int and first_ms >= 0,
             "first source timestamp missing")
    stamps = {}
    for frame in frames:
        time = frame.get("timestamp_ms")
        _require(type(time) is int and time >= first_ms and time not in stamps,
                 "invalid or duplicate source timestamp")
        stamps[time] = frame
    _require(list(stamps) == sorted(stamps), "source timestamps nonmonotonic")

    manifests: dict[str, dict] = {}
    reports: dict[str, dict] = {}
    evidence: dict[str, dict] = {}
    issues: list[dict] = []
    for variant in _VARIANTS:
        root = roots[variant]
        manifest_path = root / "retarget_manifest.json"
        qa_path = root / "retarget_qa.json"
        manifest = _read(manifest_path)
        report = _read(qa_path)
        manifests[variant], reports[variant] = manifest, report
        _require(manifest.get("variant") == variant
                 and report.get("variant") == variant,
                 "variant metadata does not match directory: " + variant)
        _require(manifest.get("data_type") ==
                 "SKINNED_HUMAN_RETARGET_DIAGNOSTIC_NOT_FINAL_MOTION",
                 "unexpected retarget representation")
        _require(manifest.get("solved_skeleton_sha256") == solved_digest,
                 "solved skeleton hash mismatch: " + variant)
        _require(manifest.get("original_video_sha256") == source
                 and manifest.get("pose_model_sha256") == model,
                 "video/model provenance mismatch")
        _require(manifest.get("commercial_approval") is False
                 and report.get("commercial_approval") is False,
                 "diagnostic pipeline may not self-approve commercial rights")
        _require(manifest.get("source_frames") == len(frames)
                 and report.get("source_frames") == len(frames),
                 "source frame counts disagree")
        _require(report.get("kinematic_fidelity") is not None,
                 "missing independently measured kinematics")
        _require(manifest.get("human_visual_review") == "PENDING"
                 and report.get("human_visual_review") == "PENDING",
                 "unexpected visual review state")
        _require(manifest.get("source_video_license") ==
                 manifests.get("male", manifest).get("source_video_license"),
                 "source license differs between variants")
        _require(report.get("joint_attachment", {}).get("status") ==
                 "TECHNICAL_PASS",
                 "joint continuity measurements missing")
        evidence[variant] = {
            "qa_sha256": _hash(qa_path),
            "manifest_sha256": _hash(manifest_path),
            "glb_sha256": _sha(manifest.get("file_sha256", {})
                              .get("retarget_review.glb"), "retarget GLB"),
            "technical_skin_roundtrip": report.get("technical_skinned_retarget"),
        }
        fidelity = report["kinematic_fidelity"]
        _require(isinstance(fidelity, dict)
                 and fidelity.get("status") in
                 {"FAIL_REVIEW_REQUIRED", "SCREENING_PASS_NOT_FINAL_QA"},
                 "invalid/missing kinematic QA state")
        all_events = fidelity.get("review_events_first_25")
        count = fidelity.get("review_event_count")
        _require(isinstance(all_events, list)
                 and type(count) is int and count >= len(all_events),
                 "invalid event-count evidence")
        _require(count == 0 or all_events,
                 "events marked but no source evidence supplied")
        if count > len(all_events):
            issues.append(_issue(source, variant, "EVENTS_TRUNCATED",
                str(count), {"total_reported": count,
                             "events_supplied": len(all_events)}))
        for event in all_events:
            _require(isinstance(event, dict), "invalid kinematic event")
            time = event.get("timestamp_ms")
            joint = event.get("joint")
            _require(type(time) is int and time in stamps,
                     "event timestamp absent from measured capture")
            _require(isinstance(joint, str)
                     and joint in {"leftKnee", "rightKnee",
                                  "leftElbow", "rightElbow"},
                     "unsupported joint event")
            _require(stamps[time].get("state") == "SOLVED_REVIEW_REQUIRED",
                     "event does not correspond to real observed pose")
            error = _number(event.get("error_degrees"), "joint angle error")
            threshold = _number(fidelity.get("screening_limit_degrees"),
                                "kinematic review threshold", lower=.000001)
            _require(error > threshold,
                     "reported blocking angle is not above review threshold")
            issues.append(_issue(source, variant, "JOINT_FLEXION_FIDELITY",
                f"{time}:{joint}", {
                    "timestamp_ms": time,
                    "source_frame": 1 + round((time - first_ms) *
                                               manifest["sample_fps"] / 1000),
                    "joint": joint, "error_degrees": error,
                    "limit_degrees": threshold,
                    "observed_source": "SOLVED_REVIEW_REQUIRED",
                }))
        issues.append(_issue(source, variant, "HUMAN_VISUAL_REVIEW_PENDING",
                             "visual", {"state": "PENDING"}))
        issues.append(_issue(source, variant, "COMMERCIAL_RIGHTS_UNAPPROVED",
                             "rights", {"license": manifest["source_video_license"],
                                        "asset_rights": manifest.get("rights_review")}))
        issues.append(_issue(source, variant, "FULL_BODY_IK_MISSING",
                             "contact", {
                                 "full_body_ik": manifest.get("full_body_ik"),
                                 "foot_contacts": manifest.get("foot_contacts"),
                                 "hand_grips": manifest.get("hand_grips"),
                             }))
    source_qa = solved.get("qa", {})
    speed_events = source_qa.get("temporal_review_events", [])
    _require(isinstance(speed_events, list), "invalid temporal source QA")
    for item in speed_events:
        _require(isinstance(item, dict), "invalid source outlier")
        ts = item.get("timestamp_ms")
        segment = item.get("segment")
        _require(type(ts) is int and ts in stamps and
                 isinstance(segment, str) and bool(segment),
                 "invalid source outlier provenance")
        speed = _number(item.get("angular_speed_deg_per_s"),
                        "source angular speed")
        issues.append(_issue(source, None, "SOURCE_ANGULAR_OUTLIER",
                             f"{ts}:{segment}", {
                                 "timestamp_ms": ts, "segment": segment,
                                 "speed_degrees_per_second": speed,
                             }))
    occlusions = source_qa.get("low_visibility_segment_samples", 0)
    _require(type(occlusions) is int and occlusions >= 0,
             "invalid low-visibility sample count")
    if occlusions:
        issues.append(_issue(source, None, "SOURCE_LOW_VISIBILITY",
                             str(occlusions), {
                                 "affected_segment_observations": occlusions,
                             }))
    issues.sort(key=lambda item: (item["kind"], item["variant"] or "",
                                  item["marker"]))
    _require(len({entry["id"] for entry in issues}) == len(issues),
             "duplicate review issue identity")
    return {
        "schema_version": "1.0.0",
        "origin": "AUTHENTIC_MEDIAPIPE_CAPTURE_REVIEW_ONLY",
        "source_video_sha256": source,
        "pose_model_sha256": model,
        "solved_skeleton_sha256": solved_digest,
        "source_video_license": manifests["male"]["source_video_license"],
        "exercises_approved": 0,
        "approved": False,
        "status": "REVIEW_REQUIRED",
        "release_gate": "BLOCKED",
        "variants": list(_VARIANTS),
        "technical_evidence": evidence,
        "issue_count": len(issues),
        "issues": issues,
        "notes": "Technical GLB fidelity is not biomechanical, visual or rights approval.",
    }


def write_real_video_review(male_dir: str | Path, female_dir: str | Path,
                            solved_path: str | Path,
                            output_path: str | Path) -> dict[str, Any]:
    payload = compile_real_video_review(male_dir, female_dir, solved_path)
    out = Path(output_path).expanduser().absolute()
    _require(out.name.endswith(".json") and
             not out.is_symlink(), "output must be a JSON file, not symlink")
    out.parent.mkdir(parents=True, exist_ok=True)
    serialized = (json.dumps(payload, ensure_ascii=False,
                             indent=2, sort_keys=True,
                             allow_nan=False) + "\n").encode("utf-8")
    if out.exists():
        _require(out.is_file() and not out.is_symlink(),
                 "unsafe prior review output")
        _require(out.read_bytes() == serialized,
                 "existing review queue differs; preserve version history")
        return {k: payload[k] for k in ("status", "release_gate", "issue_count")}
    fd, temporary = tempfile.mkstemp(prefix=".review-", suffix=".json",
                                    dir=out.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, out)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"status": payload["status"], "release_gate": "BLOCKED",
            "issue_count": payload["issue_count"],
            "review_queue_sha256": _hash(out)}
