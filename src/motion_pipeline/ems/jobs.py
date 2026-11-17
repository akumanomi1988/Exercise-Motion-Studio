"""Idempotent local registration of authorized video sources.

The source video stays on disk: it is not copied, downloaded or uploaded.
No pose extraction or media generation is performed by this module.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ems.rights import InputValidationError, validate_rights, validate_video_path

_EXERCISE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def register_source(
    source: str | Path,
    exercise_id: str,
    rights_basis: str,
    rights_evidence: str,
    jobs_dir: str | Path = "data/jobs",
) -> dict[str, Any]:
    """Register an input; idempotent by exercise, content and rights declaration.

    Rights are marked USER_ATTESTED, NEVER RIGHTS_VERIFIED.
    A registration is not a commercial-ready asset.
    """
    if not _EXERCISE_ID.fullmatch(exercise_id):
        raise InputValidationError("exercise-id must be 1-100 safe ASCII characters")
    validate_rights(rights_basis, rights_evidence)
    video = validate_video_path(source)
    source_hash = sha256_file(video)
    key = json.dumps(
        [exercise_id, source_hash, rights_basis, rights_evidence.strip()],
        separators=(",", ":"),
        ensure_ascii=True,
    )
    job_id = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    directory = (Path(jobs_dir).expanduser().resolve() / job_id)
    manifest_path = directory / "manifest.json"

    if manifest_path.exists():
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
        if current.get("job_id") != job_id:
            raise InputValidationError("existing job has inconsistent identity")
        return current

    directory.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "job_id": job_id,
        "exercise_id": exercise_id,
        "status": "REGISTERED",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "local_path": str(video),
            "sha256": source_hash,
            "size_bytes": video.stat().st_size,
            "extension": video.suffix.lower(),
        },
        "rights": {
            "basis": rights_basis,
            "evidence": rights_evidence.strip(),
            "status": "USER_ATTESTED",
            "commercial_approval": False,
        },
        "pipeline": {
            "capture": "NOT_STARTED",
            "retarget": "NOT_STARTED",
            "equipment": "NOT_STARTED",
            "render": "NOT_STARTED",
            "qa": "NOT_STARTED",
        },
    }
    # Exclusive creation avoids silently overwriting an existing job.
    try:
        with manifest_path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(manifest, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
    except FileExistsError:
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
        if current.get("job_id") != job_id:
            raise InputValidationError("concurrent registration produced a conflict")
        return current
    return manifest
