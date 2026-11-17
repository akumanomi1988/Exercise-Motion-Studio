"""I1 P-03: actual MediaPipe Tasks pose inference over locally registered video.

No fabricated motion, own video downloader, absolute 3D reconstruction, avatar
retargeting, GLB or commercial approval. Source frames come from FFmpeg; the
model .task MUST already exist locally and match an operator-provided SHA-256.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ems.jobs import sha256_file
from ems.rights import InputValidationError, validate_video_path

_JOB_ID = re.compile(r"^[0-9a-f]{24}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_LANDMARK_COUNT = 33
_CORE = (11, 12, 15, 16, 23, 24, 25, 26, 27, 28)
_MODEL_PROVENANCE = (
    "https://storage.googleapis.com/mediapipe-models/"
    "pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task"
)
_MODEL_LICENSE_EVIDENCE = "https://github.com/google-ai-edge/mediapipe/issues/6306"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise InputValidationError(message)


def _write_atomic(path: Path, data: dict[str, Any]) -> None:
    fd, tmp = tempfile.mkstemp(prefix=".capture-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _landmarks(items: Any) -> list[dict[str, float | None]]:
    _require(len(items) == _LANDMARK_COUNT, "Pose Landmarker did not return 33 joints")
    result = []
    for p in items:
        xyz = [float(getattr(p, axis)) for axis in ("x", "y", "z")]
        _require(all(math.isfinite(v) for v in xyz), "nonfinite landmark coordinates")
        attributes = []
        for key in ("visibility", "presence"):
            raw = getattr(p, key, None)
            if raw is None:
                attributes.append(None)
            else:
                value = float(raw)
                _require(math.isfinite(value) and 0 <= value <= 1,
                         "nonfinite or out-of-range confidence")
                attributes.append(value)
        result.append(dict(zip(("x", "y", "z", "visibility", "presence"),
                               [*xyz, *attributes])))
    return result


def _score(points: list[dict[str, float | None]]) -> float:
    values = [points[i]["visibility"] for i in _CORE]
    valid = [float(v) for v in values if v is not None]
    return round(sum(valid) / len(valid), 6) if valid else 0.0


def _parse_detection(result: Any, timestamp_ms: int) -> dict[str, Any]:
    image_poses = result.pose_landmarks
    world_poses = result.pose_world_landmarks
    count = len(image_poses)
    _require(len(world_poses) == count, "image/world person count mismatch")
    if count == 0:
        return {"timestamp_ms": timestamp_ms, "state": "MISSING"}
    if count > 1:
        return {"timestamp_ms": timestamp_ms, "state": "AMBIGUOUS",
                "people_detected": count}
    image_pts = _landmarks(image_poses[0])
    world_pts = _landmarks(world_poses[0])
    return {
        "timestamp_ms": timestamp_ms, "state": "DETECTED",
        "confidence_core": _score(image_pts),
        "image_landmarks": image_pts,
        "world_landmarks": world_pts,
    }


def _frames(video: Path, fps: int, resolution: int, max_frames: int):
    """Decode to a square letterboxed RGB stream. Output timestamps are CFR sample times."""
    filter_graph = (
        f"fps={fps},scale={resolution}:{resolution}:"
        f"force_original_aspect_ratio=decrease,"
        f"pad={resolution}:{resolution}:(ow-iw)/2:(oh-ih)/2"
    )
    command = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-xerror",
        "-i", str(video), "-map", "0:v:0", "-an", "-sn", "-dn",
        "-vf", filter_graph, "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1",
    ]
    try:
        proc = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except FileNotFoundError as exc:
        raise InputValidationError("FFmpeg not installed") from exc
    frame_bytes = resolution * resolution * 3
    index = 0
    try:
        assert proc.stdout is not None
        while True:
            frame = bytearray()
            while len(frame) < frame_bytes:
                piece = proc.stdout.read(frame_bytes - len(frame))
                if not piece:
                    break
                frame.extend(piece)
            if not frame:
                break
            _require(len(frame) == frame_bytes, "truncated FFmpeg rawvideo frame")
            _require(index < max_frames, "capture exceeded configured maximum frames")
            yield index, bytes(frame)
            index += 1
        _require(proc.wait(timeout=20) == 0, "FFmpeg frame extraction failed")
        _require(index > 0, "FFmpeg returned no frames")
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=20)
        if proc.stdout:
            proc.stdout.close()


def capture_registered_video(
    job_id: str, model_path: str | Path, model_sha256: str,
    jobs_dir: str | Path = "data/jobs", sample_fps: int = 8,
    resolution: int = 512, max_duration_s: int = 120,
) -> dict[str, Any]:
    """Run CPU-only inference and persist raw 2D+hip-relative 3D observations.

    Returns REVIEW_REQUIRED even for strong detections: no global scale, IK,
    contacts, visual QA or license approval has taken place.
    """
    _require(bool(_JOB_ID.fullmatch(job_id)), "invalid registered job-id")
    _require(bool(_SHA256.fullmatch(model_sha256)), "model SHA-256 must be 64 lowercase hex")
    _require(type(sample_fps) is int and 2 <= sample_fps <= 30,
             "sample-fps must be 2..30")
    _require(type(resolution) is int and 256 <= resolution <= 1024
             and resolution % 2 == 0, "resolution must be even in [256,1024]")
    _require(type(max_duration_s) is int and 1 <= max_duration_s <= 1800,
             "max-duration-s must be 1..1800")

    folder = Path(jobs_dir).expanduser().resolve() / job_id
    manifest_path = folder / "manifest.json"
    _require(manifest_path.is_file() and not manifest_path.is_symlink(),
             "registered manifest missing or unsafe")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _require(isinstance(manifest, dict) and manifest.get("job_id") == job_id,
             "registered manifest identity mismatch")
    _require(manifest.get("rights", {}).get("status") == "USER_ATTESTED"
             and manifest["rights"].get("basis") in {"owned", "licensed", "cc-by", "cc0"},
             "registered source rights declaration required")
    source = manifest.get("source", {})
    video = validate_video_path(source.get("local_path", ""))
    source_hash = sha256_file(video)
    _require(source_hash == source.get("sha256"), "source video changed since registration")
    probe = manifest.get("media_probe", {})
    _require(probe.get("validation") == "FULL_STREAM_DECODED"
             and probe.get("source_sha256") == source_hash,
             "real media probe required before inference")
    duration = float(probe.get("duration_seconds", 0))
    _require(math.isfinite(duration) and 0 < duration <= max_duration_s,
             "video duration exceeds configured capture limit")

    model = Path(model_path).expanduser().resolve(strict=True)
    _require(model.is_file() and model.suffix == ".task", "local .task bundle required")
    model_hash = sha256_file(model)
    _require(model_hash == model_sha256, "model SHA-256 mismatch; inference refused")

    try:
        import mediapipe as mp
        import numpy as np
    except ImportError as exc:
        raise InputValidationError(
            "MediaPipe and NumPy unavailable; install optional pose dependencies"
        ) from exc

    # VIDEO mode tracks temporal identity, but more than one person is ambiguous.
    vision = mp.tasks.vision
    options = vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(model)),
        running_mode=vision.RunningMode.VIDEO, num_poses=2,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_segmentation_masks=False,
    )
    observations: list[dict[str, Any]] = []
    with vision.PoseLandmarker.create_from_options(options) as detector:
        for index, rgb in _frames(video, sample_fps, resolution,
                                  max_duration_s * sample_fps + sample_fps):
            pixels = np.frombuffer(rgb, dtype=np.uint8).reshape(
                (resolution, resolution, 3)
            ).copy()
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=pixels)
            timestamp_ms = round(index * 1000 / sample_fps)
            prediction = detector.detect_for_video(image, timestamp_ms)
            observations.append(_parse_detection(prediction, timestamp_ms))

    _require(sha256_file(video) == source_hash, "source changed during inference")
    _require(sha256_file(model) == model_hash, "model changed during inference")
    total = len(observations)
    detected = [f for f in observations if f["state"] == "DETECTED"]
    ambiguous = sum(f["state"] == "AMBIGUOUS" for f in observations)
    low = sum(f["confidence_core"] < 0.5 for f in detected)
    coverage = len(detected) / total
    confidence = sum(f["confidence_core"] for f in detected) / len(detected) if detected else 0.0

    qa = {
        "status": "REVIEW_REQUIRED",
        "total_frames": total,
        "detected_frames": len(detected),
        "missing_frames": total - len(detected) - ambiguous,
        "ambiguous_frames": ambiguous,
        "low_confidence_frames": low,
        "detection_coverage": round(coverage, 6),
        "mean_core_visibility": round(confidence, 6),
        "warnings": (
            ["One-camera world landmarks are hip-relative, not calibrated world space."]
            + (["Multiple people detected; subject identity requires review."] if ambiguous else [])
            + (["Low/missing landmark visibility; review occlusion and tracking."] if low or coverage < 0.95 else [])
        ),
        "gate_g1": "NOT_EVALUATED",
        "commercial_approval": False,
    }
    pose = {
        "schema_version": "1.0.0",
        "data_type": "MEDIAPIPE_RAW_POSE_OBSERVATIONS",
        "method": "video_inference_real",
        "job_id": job_id, "exercise_id": manifest["exercise_id"],
        "source_sha256": source_hash,
        "model": {
            "sha256": model_hash, "framework": "mediapipe",
            "framework_version": getattr(mp, "__version__", "unknown"),
            "upstream_bundle_url": _MODEL_PROVENANCE,
            "upstream_license_evidence": _MODEL_LICENSE_EVIDENCE,
            "distribution_review": "PENDING",
        },
        "space": {
            "image": "NORMALIZED_RGB_LETTERBOX_0_TO_1",
            "world": "MEDIAPIPE_WORLD_HIP_RELATIVE_METERS_UNCALIBRATED",
            "absolute_root_motion": False,
            "retarget_approved": False,
        },
        "video": {
            "input_duration_seconds": duration,
            "sampling_fps": sample_fps, "letterbox_resolution": resolution,
            "timestamps": "CFR_TIMESTAMP_MS_FROM_FFMPEG_FPS_FILTER",
            "sampling_note": "CFR resampling; original VFR/source timestamps not preserved",
        },
        "frames": observations,
        "qa": qa,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    pose_path = folder / "pose_raw.json"
    _write_atomic(pose_path, pose)
    pose_sha256 = sha256_file(pose_path)
    manifest["pose_capture"] = {
        "artifact": "pose_raw.json", "sha256": pose_sha256,
        "model_sha256": model_hash, "qa": qa,
    }
    manifest.setdefault("pipeline", {})["capture"] = "REVIEW_REQUIRED"
    _write_atomic(manifest_path, manifest)
    return {
        "job_id": job_id, "status": "CAPTURED_REVIEW_REQUIRED",
        "artifact": "pose_raw.json", "sha256": pose_sha256,
        "qa": qa, "rights_status": manifest["rights"]["status"],
        "commercial_approval": False,
    }
