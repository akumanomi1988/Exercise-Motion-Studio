"""Real FFprobe/FFmpeg validation of an already registered, authorized local video.

This module only verifies the media and records provenance. It does not perform
pose inference, approve rights, or mark a capture/GLB gate as passed.
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from ems.jobs import sha256_file
from ems.rights import InputValidationError, validate_video_path

_JOB_ID = re.compile(r"^[a-f0-9]{24}$")


def _run(args: list[str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout_seconds, check=False,
        )
    except FileNotFoundError as exc:
        raise InputValidationError(f"required media executable unavailable: {args[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise InputValidationError(f"media operation timed out after {timeout_seconds}s") from exc
    if result.returncode != 0:
        # File paths and untrusted metadata can occur in process diagnostics.
        # Never store or return raw FFmpeg output as part of a public manifest.
        raise InputValidationError(
            f"{Path(args[0]).name} exited with code {result.returncode}; "
            "inspect the local file and tool logs"
        )
    return result


def _positive_float(raw: object, label: str) -> float:
    try:
        number = float(raw)
    except (ValueError, TypeError, OverflowError) as exc:
        raise InputValidationError(f"invalid {label} from ffprobe") from exc
    if not math.isfinite(number) or number <= 0:
        raise InputValidationError(f"invalid {label} from ffprobe")
    return number


def _fps(stream: dict[str, Any]) -> float:
    for key in ("avg_frame_rate", "r_frame_rate"):
        try:
            value = Fraction(str(stream.get(key, "0/0")))
            if value > 0 and math.isfinite(float(value)):
                return round(float(value), 6)
        except (ValueError, ZeroDivisionError, OverflowError):
            pass
    raise InputValidationError("ffprobe did not return a usable video FPS")


def _metadata(video: Path, timeout_seconds: int) -> dict[str, Any]:
    raw = _run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format",
         "-of", "json", str(video)], timeout_seconds,
    ).stdout
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InputValidationError("ffprobe returned invalid JSON") from exc
    streams = doc.get("streams", [])
    if not isinstance(streams, list):
        raise InputValidationError("ffprobe streams must be an array")
    video_streams = [
        s for s in streams
        if isinstance(s, dict)
        and s.get("codec_type") == "video"
        and not s.get("disposition", {}).get("attached_pic")
    ]
    if len(video_streams) != 1:
        raise InputValidationError("exactly one primary video stream is required")
    stream = video_streams[0]
    try:
        width, height, index = int(stream["width"]), int(stream["height"]), int(stream["index"])
    except (KeyError, ValueError, TypeError, OverflowError) as exc:
        raise InputValidationError("ffprobe returned invalid stream dimensions/index") from exc
    if not (0 < width <= 8192 and 0 < height <= 8192 and index >= 0):
        raise InputValidationError("invalid or unsupported video dimensions/index")
    # Video stream duration may be absent in MOV/MP4; format is a fallback.
    duration_raw = stream.get("duration") or doc.get("format", {}).get("duration")
    duration = _positive_float(duration_raw, "duration")
    fps = _fps(stream)
    if fps > 1000:
        raise InputValidationError("unsupported video FPS above 1000")
    codec = stream.get("codec_name")
    if not isinstance(codec, str) or not codec:
        raise InputValidationError("video codec is unidentified")
    count = stream.get("nb_frames")
    if count not in (None, "N/A"):
        try:
            count = int(count)
            if count <= 0:
                raise ValueError("nonpositive")
        except (TypeError, ValueError, OverflowError) as exc:
            raise InputValidationError("invalid frame count from ffprobe") from exc
    else:
        count = None
    return {
        "stream_index": index, "codec": codec, "width": width, "height": height,
        "duration_seconds": round(duration, 6), "average_fps": fps,
        "declared_frame_count": count,
        "frame_rate_note": "FFprobe average; VFR timestamps not reconstructed",
    }


def probe_registered_video(
    job_id: str, jobs_dir: str | Path = "data/jobs", decode_timeout_s: int = 300,
) -> dict[str, Any]:
    """Verify identity, probe real media, decode every video frame, update manifest.

    FFmpeg validates decodability. Passing is NOT pose extraction or visual QA.
    Original source content and rights state must remain unchanged.
    """
    if not _JOB_ID.fullmatch(job_id):
        raise InputValidationError("job-id must be a 24-character hexadecimal identifier")
    if not (1 <= decode_timeout_s <= 3600):
        raise InputValidationError("decode-timeout-s must be between 1 and 3600")
    directory = Path(jobs_dir).expanduser().resolve() / job_id
    manifest_file = directory / "manifest.json"
    if manifest_file.is_symlink() or not manifest_file.is_file():
        raise InputValidationError("registered job manifest is missing or unsafe")
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise InputValidationError("registered job manifest is invalid") from exc
    if not isinstance(manifest, dict) or manifest.get("job_id") != job_id:
        raise InputValidationError("registered job identity is inconsistent")
    if manifest.get("rights", {}).get("status") != "USER_ATTESTED":
        raise InputValidationError("unexpected source rights state")
    source = manifest.get("source", {})
    video = validate_video_path(source.get("local_path", ""))
    before = sha256_file(video)
    if before != source.get("sha256") or video.stat().st_size != source.get("size_bytes"):
        raise InputValidationError("registered video changed since initial registration")

    metadata = _metadata(video, min(decode_timeout_s, 30))
    decoded = _run(
        ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-xerror",
         "-i", str(video), "-map", f"0:{metadata['stream_index']}",
         "-an", "-sn", "-dn", "-progress", "pipe:1", "-f", "null", "-"],
        decode_timeout_s,
    )
    frame_values = re.findall(r"(?m)^frame=(\d+)\s*$", decoded.stdout)
    decoded_frames = int(frame_values[-1]) if frame_values else 0
    if decoded_frames <= 0:
        raise InputValidationError("FFmpeg did not confirm any decoded video frames")
    if sha256_file(video) != before or video.stat().st_size != source["size_bytes"]:
        raise InputValidationError("video changed while being decoded; result discarded")
    metadata["decoded_frames"] = decoded_frames
    metadata["validation"] = "FULL_STREAM_DECODED"
    metadata["probe_at_utc"] = datetime.now(timezone.utc).isoformat()
    metadata["source_sha256"] = before

    manifest["media_probe"] = metadata
    manifest.setdefault("pipeline", {})["probe"] = "PASS"
    # Atomic replacement avoids persisting half-written JSON on interruption.
    fd, name = tempfile.mkstemp(prefix=".probe-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(manifest, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, manifest_file)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return {
        "job_id": job_id, "status": "VIDEO_PROBED", "media_probe": metadata,
        "commercial_approval": False,
        "capture": manifest["pipeline"].get("capture", "NOT_STARTED"),
    }
