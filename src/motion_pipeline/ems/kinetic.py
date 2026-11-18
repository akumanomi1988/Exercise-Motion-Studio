"""Offline G5 equipment inventory from EXACT Kinetic Spanish MIT data snapshot.

Input is local authorized JSON; no YouTube media/thumbnail, RepDB, or other
dataset is ever fetched or embedded. Generated entries are NOT approved.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from collections import Counter
from pathlib import Path
from ems.rights import InputValidationError

UPSTREAM = "kinetic-place/exercises-db"
COMMIT = "75d59701c749243f522149d5edd63ec4c6870e5e"
BLOBS = {
    "es/exercises.json": "ae8835aadbcbb05a06d0a75d29c7b604045c09b4",
    "es/equipment.json": "5b117cae1a416f1b4badb6eba81ae45634cebef1",
}
COUNTS = {"exercises": 908, "equipment": 44}


def require(ok, why):
    if not ok:
        raise InputValidationError("kinetic-snapshot: " + why)


def valid_id(value, where):
    require(isinstance(value, str), "UUID must be a string: " + where)
    try:
        parsed = uuid.UUID(value)
    except ValueError as exc:
        raise InputValidationError("kinetic-snapshot: invalid UUID " + where) from exc
    require(str(parsed) == value.lower(), "noncanonical UUID: " + where)
    return str(parsed)


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") +
                        b"\0" + data).hexdigest()


def read_pinned(path, source_path):
    require(path.is_file() and not path.is_symlink(),
            "unsafe/missing input " + source_path)
    require(path.stat().st_size <= 10_000_000, "oversized input " + source_path)
    data = path.read_bytes()
    sha1 = git_blob(data)
    require(sha1 == BLOBS[source_path],
            "pinned upstream Git blob mismatch: " + source_path)
    try:
        records = json.loads(data.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise InputValidationError("kinetic-snapshot: corrupt JSON " +
                                   source_path) from exc
    require(isinstance(records, list), "source must be an array")
    return records, {
        "path": source_path, "git_blob_sha1": sha1,
        "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
    }


def build_index(exercises, equipment, evidence=None):
    """Pure metadata contract: no source media links survive whitelisting."""
    require(isinstance(exercises, list) and isinstance(equipment, list),
            "exercises/equipment arrays required")
    equipment_index = {}
    family_counts = Counter()
    for obj in equipment:
        require(isinstance(obj, dict), "bad equipment object")
        eid = valid_id(obj.get("id"), "equipment")
        require(eid not in equipment_index, "duplicate equipment UUID " + eid)
        name, family = obj.get("name"), obj.get("family")
        require(isinstance(name, str) and name.strip() and len(name) <= 180,
                "invalid equipment name " + eid)
        require(isinstance(family, str) and family.strip() and
                len(family) <= 80, "invalid equipment family " + eid)
        equipment_index[eid] = {
            "id": eid, "name_es": name, "family": family,
            "referenced_by_exercises": 0, "asset_id": None,
            "asset_status": "MISSING_UNAPPROVED",
        }
        family_counts[family] += 1

    used_ids = set()
    used_slugs = set()
    rows = []
    categories = Counter()
    no_equipment = 0
    for obj in exercises:
        require(isinstance(obj, dict), "bad exercise object")
        xid = valid_id(obj.get("id"), "exercise")
        require(xid not in used_ids, "duplicate exercise UUID " + xid)
        used_ids.add(xid)
        name, slug = obj.get("name"), obj.get("slug")
        require(isinstance(name, str) and name.strip() and len(name) <= 250,
                "invalid exercise name: " + xid)
        require(isinstance(slug, str) and slug.strip() and
                len(slug) <= 180 and slug not in used_slugs,
                "invalid/duplicate exercise slug: " + xid)
        used_slugs.add(slug)
        refs = obj.get("equipment", [])
        require(isinstance(refs, list), "bad equipment references: " + xid)
        rel = set()
        for item in refs:
            require(isinstance(item, dict), "bad equipment link: " + xid)
            rid = valid_id(item.get("id"), "exercise equipment")
            require(rid in equipment_index,
                    "reference to nonexistent Kinetic equipment: " + rid)
            require(rid not in rel, "duplicate equipment link: " + xid)
            rel.add(rid)
            equipment_index[rid]["referenced_by_exercises"] += 1
        category = obj.get("category")
        require(category is None or
                (isinstance(category, str) and len(category) <= 80),
                "invalid category")
        categories[str(category or "unspecified")] += 1
        if not rel:
            no_equipment += 1
        # No youtube field, thumbnail, URLs, guides or source footage.
        rows.append({
            "kinetic_exercise_id": xid, "name_es": name, "slug": slug,
            "category": category, "equipment_ids": sorted(rel),
            "asset_state": "NOT_GENERATED", "approved": False,
        })

    return {
        "schema_version": "1.0.0",
        "kind": "KINETIC_PINNED_METADATA_ONLY_EQUIPMENT_BACKLOG",
        "source": {
            "repository": UPSTREAM, "commit": COMMIT, "locale": "es",
            "license": "MIT", "copyright": "Copyright (c) 2026 Kinetic.place",
            "license_applies_to": "REPOSITORY_DATA_ONLY",
            "youtube_media_copied": False, "repdb_imported": False,
            "input_evidence": evidence or {},
        },
        "g5": "IN_PROGRESS", "g6": "NOT_APPROVED",
        "exercise_count": len(rows),
        "equipment_type_count": len(equipment_index),
        "equipment_association_count": sum(
            x["referenced_by_exercises"] for x in equipment_index.values()),
        "exercises_without_equipment": no_equipment,
        "unmapped_equipment_types": len(equipment_index),
        "approved_exercises": 0,
        "families": dict(sorted(family_counts.items())),
        "categories": dict(sorted(categories.items())),
        "equipment": sorted(equipment_index.values(), key=lambda x: x["id"]),
        "exercises": sorted(rows, key=lambda x: x["kinetic_exercise_id"]),
    }


def audit(exercise_path, equipment_path):
    exercises, e = read_pinned(exercise_path, "es/exercises.json")
    equipment, q = read_pinned(equipment_path, "es/equipment.json")
    report = build_index(exercises, equipment, {
        "es/exercises.json": e, "es/equipment.json": q,
    })
    require(report["exercise_count"] == COUNTS["exercises"],
            "pinned snapshot has unexpected exercise count")
    require(report["equipment_type_count"] == COUNTS["equipment"],
            "pinned snapshot has unexpected equipment count")
    return report


def write_inventory(exercise_path, equipment_path, output_path):
    inventory = audit(Path(exercise_path), Path(equipment_path))
    dest = Path(output_path).expanduser().absolute()
    require(dest.suffix.lower() == ".json" and not dest.is_symlink(),
            "output must be a regular JSON file")
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = (json.dumps(inventory, ensure_ascii=False, sort_keys=True,
                          indent=2, allow_nan=False) + "\n").encode("utf-8")
    if dest.exists():
        require(dest.is_file() and not dest.is_symlink(),
                "unsafe existing destination")
        require(dest.read_bytes() == content,
                "immutable source inventory changed; write new version")
    else:
        fd, name = tempfile.mkstemp(prefix=".kinetic-", suffix=".json",
                                   dir=dest.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, dest)
        finally:
            if os.path.exists(name):
                os.unlink(name)
    return {
        "source_commit": COMMIT,
        "exercise_count": inventory["exercise_count"],
        "equipment_type_count": inventory["equipment_type_count"],
        "unmapped_equipment_types": inventory["unmapped_equipment_types"],
        "approved_exercises": 0,
        "sha256": hashlib.sha256(content).hexdigest(),
        "g5": "IN_PROGRESS", "g6": "NOT_APPROVED",
    }
