"""Fail-closed input validation and rights-attestation primitives.

Operator attestations are not legal/license approval. They only permit
local registration for subsequent review and processing.
"""

from pathlib import Path

ALLOWED_RIGHTS_BASES = frozenset({"owned", "licensed", "cc-by", "cc0"})
ALLOWED_EXTENSIONS = frozenset({".mp4", ".mov", ".webm"})


class InputValidationError(ValueError):
    """A source cannot be registered without resolving the cause."""


def validate_video_path(source: str | Path) -> Path:
    candidate = Path(source).expanduser().resolve(strict=True)
    if not candidate.is_file():
        raise InputValidationError("source must be a regular local file")
    if candidate.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise InputValidationError("unsupported video extension (MP4, MOV, WebM)")
    if candidate.stat().st_size == 0:
        raise InputValidationError("video file is empty")
    # Registration is NOT video decoding or authenticity verification.
    return candidate


def validate_rights(rights_basis: str, evidence: str) -> None:
    if rights_basis not in ALLOWED_RIGHTS_BASES:
        raise InputValidationError("rights basis must be one of: owned, licensed, cc-by, cc0")
    if not evidence or not evidence.strip():
        raise InputValidationError("rights evidence/reference is mandatory")
    if len(evidence) > 2048:
        raise InputValidationError("rights evidence exceeds 2048 characters")
