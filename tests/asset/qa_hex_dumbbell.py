"""Blender headless round-trip and visual-image sanity checks for one generated asset.

These checks are technical, not a substitute for human visual inspection.
Run: blender -b --python tests/asset/qa_hex_dumbbell.py -- --asset-dir <directory>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_asset(folder: Path) -> dict:
    meta = json.loads((folder / "asset.json").read_text(encoding="utf-8"))
    assert meta["asset_id"].startswith("ems.equipment.dumbbell.hex.")
    assert meta["unit"] == "meter"
    assert meta["licenses"]["status"] == "PENDING"
    assert meta["licenses"]["distribution_approved"] is False
    assert len(meta["collision_shapes"]) == 3
    assert len(meta["contact_surfaces"]) == 2
    for name in ("asset.blend", "asset.glb", "preview.png"):
        path = folder / name
        assert path.stat().st_size > 1024, f"asset file too small: {name}"
        assert _hash(path) == meta["file_sha256"][name], f"hash mismatch: {name}"

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(folder / "asset.glb"))
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    assert len(meshes) >= 5, f"GLB round-trip lost parts: {len(meshes)}"
    assert all(any(slot.material for slot in m.material_slots) for m in meshes), "missing material"
    vertices = [
        o.matrix_world @ vertex.co
        for o in meshes for vertex in o.data.vertices
    ]
    assert vertices and all(
        math.isfinite(component) for v in vertices for component in v
    ), "nonfinite GLB geometry"
    span = [max(v[i] for v in vertices) - min(v[i] for v in vertices)
            for i in range(3)]
    dims = meta["dimensions_m"]
    # A hexagon's cross-section is smaller than its circumscribed diameter.
    # The expected metadata is an envelope, not a rectangular mesh bounding box.
    assert 0.90 * dims["length_x"] <= span[0] <= 1.10 * dims["length_x"], span
    assert 0.70 * dims["width_y"] <= span[1] <= 1.10 * dims["width_y"], span
    assert 0.70 * dims["height_z"] <= span[2] <= 1.10 * dims["height_z"], span

    image = bpy.data.images.load(str(folder / "preview.png"), check_existing=False)
    assert image.size[0] == 512 and image.size[1] == 512, image.size[:]
    # Verify real pixel data differs across the image; no blank render.
    # Human still needs to inspect composition and visual acceptability.
    pixels = image.pixels
    samples = [tuple(pixels[i:i + 3]) for i in
               range(0, len(pixels) - 3, max(4, len(pixels) // 400))]
    assert len({tuple(round(float(c), 2) for c in rgb) for rgb in samples}) > 6, \
        "render appears uniform/blank"

    # The editable .blend must also open and contain the procedural meshes.
    bpy.ops.wm.open_mainfile(filepath=str(folder / "asset.blend"))
    authored_meshes = [o for o in bpy.context.scene.objects
                       if o.type == "MESH" and o.get("ems_export")]
    assert len(authored_meshes) == 5, "editable Blender source has wrong parts"
    result = {
        "technical_roundtrip": "PASS",
        "glb_mesh_count": len(meshes),
        "editable_mesh_count": len(authored_meshes),
        "mesh_dimensions_m": [round(x, 6) for x in span],
        "png_size": [512, 512],
        "png_nonuniform": True,
        "human_visual_review": "PENDING",
        "rights_review": "PENDING",
        "commercial_approval": False,
        "note": "One unanimated original equipment asset. No avatar, exercise or motion capture.",
    }
    meta["qa"]["roundtrip"] = "PASS"
    meta["qa"]["human_visual_review"] = "PENDING"
    meta["qa"]["commercial_approval"] = False
    (folder / "asset.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (folder / "qa_report.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p.add_argument("--asset-dir", type=Path, required=True)
    args = p.parse_args(argv)
    result = validate_asset(args.asset_dir.expanduser().resolve())
    print("EMS_ASSET_QA=" + json.dumps(result))
