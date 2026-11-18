"""AG0 asset manifest integrity boundary; no geometry or commercial approval claims.

Binary glTF, Blender reopening, visual inspection and rig interoperability must
be checked independently. A JSON manifest is never sufficient for AG0/G2 PASS.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from ems.rights import InputValidationError

_ID = re.compile(r"^ems\.[a-z][a-z0-9_.-]{3,120}$")
_SHA = re.compile(r"^[a-f0-9]{64}$")
_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
_FILE_TYPES = {"editable": ".blend", "distribution": ".glb", "thumbnail": ".png"}


def _check(ok: bool, description: str) -> None:
    if not ok:
        raise InputValidationError(f"asset manifest: {description}")


def _vector(value: object, name: str, unit_axis: bool = False) -> None:
    _check(isinstance(value, list) and len(value) == 3, f"{name} must be a 3-vector")
    _check(all(type(x) in (int, float) and math.isfinite(x) for x in value),
           f"{name} components must be finite numbers")
    if unit_axis:
        length = math.sqrt(sum(x * x for x in value))
        _check(abs(length - 1) < 1e-4, f"{name} must be a unit vector")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _approved_qa_record(root: Path, qa: object) -> bool:
    """Check signed review metadata AND integrity of the archived QA record.

    This is an integrity/attestation boundary, not independent GLB rendering or
    proof that a named reviewer is an authorized person. Commercial publishing
    must additionally verify reviewer identity and externally rerun Blender QA.
    """
    if not isinstance(qa, dict):
        return False
    if (qa.get("human_visual_review") != "APPROVED"
            or qa.get("commercial_approval") is not True
            or qa.get("roundtrip", qa.get("glb_roundtrip")) != "PASS"):
        return False
    if not (isinstance(qa.get("reviewer"), str) and qa["reviewer"].strip()
            and isinstance(qa.get("reviewed_at"), str) and qa["reviewed_at"].strip()
            and isinstance(qa.get("report_sha256"), str)
            and bool(_SHA.fullmatch(qa["report_sha256"]))):
        return False
    record = root / "qa_report.json"
    if (not record.is_file() or record.is_symlink()
            or record.resolve().parent != root
            or not (2 < record.stat().st_size <= 512 * 1024)
            or _sha256(record) != qa["report_sha256"]):
        return False
    try:
        report = json.loads(record.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError):
        return False
    return (isinstance(report, dict)
            and report.get("technical_roundtrip") == "PASS"
            and report.get("human_visual_review") == "APPROVED"
            and report.get("commercial_approval") is True
            and report.get("reviewer") == qa["reviewer"]
            and report.get("reviewed_at") == qa["reviewed_at"])


def inspect_asset_folder(folder: str | Path, require_commercial: bool = False) -> dict[str, Any]:
    """Fail closed on unsafe paths, bad provenance, missing files or unapproved rights.

    Successful noncommercial mode means *manifest integrity only*.
    It says nothing about whether the files really contain an armature or GLB.
    """
    root = Path(folder).expanduser().resolve(strict=True)
    _check(root.is_dir(), "asset folder must be a directory")
    path = root / "asset.json"
    _check(path.is_file() and not path.is_symlink(), "missing or unsafe asset.json")
    _check(path.stat().st_size <= 512 * 1024, "asset.json exceeds 512 KiB")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise InputValidationError("asset manifest: invalid UTF-8 JSON") from exc
    _check(isinstance(data, dict), "top-level object required")
    asset_id = data.get("asset_id")
    _check(isinstance(asset_id, str) and bool(_ID.fullmatch(asset_id)), "invalid asset ID")
    _check(data.get("schema_version") == "1.0", "unsupported schema version")
    version = data.get("version")
    _check(isinstance(version, str) and bool(_VERSION.fullmatch(version)), "invalid asset version")
    _check(data.get("unit") == "meter", "unit must be meter")
    _check(isinstance(data.get("category"), str) and bool(data["category"]), "category missing")
    _check(isinstance(data.get("source"), dict) and data["source"].get("kind") in
           {"ORIGINAL_PROCEDURAL", "VERIFIED_THIRD_PARTY"}, "unsupported source provenance")
    _check(isinstance(data.get("licenses"), dict), "license section missing")
    rights = data["licenses"]
    _check(rights.get("status") in {"PENDING", "APPROVED", "REJECTED"}, "invalid rights state")
    _check(type(rights.get("distribution_approved")) is bool, "approval must be boolean")

    dims = data.get("dimensions_m")
    _check(isinstance(dims, dict), "dimensions_m missing")
    for dim in ("length_x", "width_y", "height_z"):
        v = dims.get(dim)
        _check(type(v) in (int, float) and math.isfinite(v) and v > 0,
               f"invalid dimension {dim}")

    for key in ("grip_points", "attachment_points"):
        points = data.get(key)
        _check(isinstance(points, list), f"{key} must be a list")
        ids: set[str] = set()
        for p in points:
            _check(isinstance(p, dict), f"{key} entries must be objects")
            ident = p.get("id")
            _check(isinstance(ident, str) and ident not in ids and bool(ident),
                   f"duplicate/invalid {key} identifier")
            ids.add(ident)
            _vector(p.get("position_m"), f"{key}.{ident}.position_m")
            if key == "grip_points":
                _vector(p.get("axis"), f"{key}.{ident}.axis", unit_axis=True)

    shapes = data.get("collision_shapes")
    _check(isinstance(shapes, list), "collision_shapes must be a list")
    for shape in shapes:
        _check(isinstance(shape, dict) and shape.get("shape") == "cylinder",
               "only cylinder collision primitives currently supported")
        _vector(shape.get("center_m"), "collision center")
        _vector(shape.get("axis"), "collision axis", unit_axis=True)
        for key in ("radius_m", "length_m"):
            v = shape.get(key)
            _check(type(v) in (int, float) and math.isfinite(v) and v > 0,
                   f"invalid collider {key}")
    for contact in data.get("contact_surfaces", []):
        _check(isinstance(contact, dict), "invalid contact surface")
        _vector(contact.get("point_m"), "contact point")
        _vector(contact.get("normal"), "contact normal", unit_axis=True)

    files = data.get("models")
    hashes = data.get("file_sha256")
    _check(isinstance(files, dict) and isinstance(hashes, dict), "models/hashes missing")
    for role, ext in _FILE_TYPES.items():
        name = files.get(role)
        _check(isinstance(name, str) and name == Path(name).name and "/" not in name and "\\" not in name and name.endswith(ext),
               f"unsafe {role} model path")
        item = root / name
        _check(item.is_file() and not item.is_symlink() and item.resolve().parent == root,
               f"missing/unsafe {role} file")
        _check(item.stat().st_size > 1024, f"{role} file too small")
        digest = hashes.get(name)
        _check(isinstance(digest, str) and bool(_SHA.fullmatch(digest)),
               f"missing/invalid {role} SHA-256")
        _check(_sha256(item) == digest, f"{role} SHA-256 mismatch")

    rights_approved = (
        rights["status"] == "APPROVED"
        and rights["distribution_approved"] is True
        and isinstance(rights.get("reviewer"), str) and bool(rights["reviewer"].strip())
        and isinstance(rights.get("reviewed_at"), str) and bool(rights["reviewed_at"])
        and isinstance(rights.get("evidence_sha256"), str)
        and bool(_SHA.fullmatch(rights["evidence_sha256"]))
    )
    qa_record_approved = _approved_qa_record(root, data.get("qa"))
    if require_commercial:
        _check(rights_approved, "commercial distribution blocked: rights review incomplete")
        _check(qa_record_approved, "commercial distribution blocked: visual/geometry QA evidence incomplete")
    return {
        "asset_id": asset_id, "version": version,
        "status": "MANIFEST_INTEGRITY_PASS",
        "rights_status": rights["status"],
        # These are recorded attestations, NOT a real-time mesh/render check.
        "commercial_distribution_allowed": bool(rights_approved and qa_record_approved),
        "qa_record_integrity_pass": bool(qa_record_approved),
        "external_geometry_validation": "NOT_PERFORMED",
        "visual_review": "NOT_PERFORMED",
    }


def scan_asset_catalog(root: str | Path) -> list[dict[str, Any]]:
    """List manifests with duplicate-ID detection; one bad asset aborts discovery."""
    directory = Path(root).expanduser().resolve(strict=True)
    _check(directory.is_dir(), "catalog root must be directory")
    by_id: set[str] = set()
    result = []
    for manifest in sorted(directory.rglob("asset.json")):
        item = inspect_asset_folder(manifest.parent)
        _check(item["asset_id"] not in by_id, f"duplicate ID {item['asset_id']}")
        by_id.add(item["asset_id"])
        result.append(item)
    return result
