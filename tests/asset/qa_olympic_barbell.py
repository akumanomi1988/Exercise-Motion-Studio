"""Headless Blender checks: annular plate topology, GLB reimport and preview.

Technical-only; a loaded barbell must still pass retarget and human rights review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(folder: Path) -> dict:
    meta = json.loads((folder / "asset.json").read_text(encoding="utf-8"))
    assert meta["asset_id"].startswith("ems.equipment.barbell.olympic.")
    assert meta["unit"] == "meter"
    assert meta["licenses"]["status"] == "PENDING"
    assert meta["licenses"]["distribution_approved"] is False
    assert meta["qa"]["commercial_approval"] is False
    load = meta["variant"]["plates_per_side"]
    assert 0 <= load <= 4
    assert meta["part_mesh_count"] == 7 + 2 * load
    assert len(meta["grip_points"]) == 2
    grips = meta["grip_points"]
    assert grips[0]["position_m"] == [-.42, 0, 0]
    assert grips[1]["position_m"] == [.42, 0, 0]
    assert meta["variant"]["nominal_total_mass_kg"] == (
        20 + 2 * load * meta["variant"]["nominal_plate_mass_kg"]
    )
    for name in ("asset.blend", "asset.glb", "preview.png"):
        path = folder / name
        assert path.is_file() and path.stat().st_size > 1024, name
        assert sha(path) == meta["file_sha256"][name], name

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(folder / "asset.glb"))
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    assert len(meshes) == meta["part_mesh_count"], (
        "import lost a part", len(meshes)
    )
    assert all(len(obj.material_slots) > 0 and
               any(slot.material for slot in obj.material_slots)
               for obj in meshes), "GLB lost materials"
    points = [obj.matrix_world @ vertex.co
              for obj in meshes for vertex in obj.data.vertices]
    assert points and all(math.isfinite(v) for p in points for v in p)
    span = [max(p[i] for p in points) - min(p[i] for p in points)
            for i in range(3)]
    dims = meta["dimensions_m"]
    for i, key in enumerate(("length_x", "width_y", "height_z")):
        assert abs(span[i] - dims[key]) < .005, (key, span[i], dims[key])

    plates = [obj for obj in meshes if " plate " in obj.name.lower()]
    assert len(plates) == 2 * load, "plate symmetry lost"
    # Annular plates must have actual center holes, not solid cylinders
    # intersecting the Olympic sleeve.
    for plate in plates:
        radial = [
            math.hypot(float(v.co.y), float(v.co.z))
            for v in plate.data.vertices
        ]
        assert radial and min(radial) >= .0249, (
            "plate through-hole missing", plate.name, min(radial)
        )
        assert len(plate.data.vertices) >= 256, "plate topology simplified away"

    preview = bpy.data.images.load(str(folder / "preview.png"),
                                   check_existing=False)
    assert list(preview.size) == [960, 480], preview.size[:]
    pixels = preview.pixels
    colors = set()
    step = max(4, (len(pixels) // 800 // 4) * 4)
    for i in range(0, len(pixels) - 4, step):
        colors.add(tuple(round(float(c), 2) for c in pixels[i:i + 3]))
    assert len(colors) > 12, "technical preview appears blank"

    bpy.ops.wm.open_mainfile(filepath=str(folder / "asset.blend"))
    authored = [o for o in bpy.context.scene.objects
                if o.type == "MESH" and o.get("ems_export")]
    assert len(authored) == meta["part_mesh_count"], "editable source lost parts"
    authored_plates = [o for o in authored if o.get("part_type") == "plate"]
    assert len(authored_plates) == 2 * load
    result = {
        "technical_roundtrip": "PASS",
        "glb_mesh_count": len(meshes),
        "editable_mesh_count": len(authored),
        "plate_annular_holes": "CHECKED" if load else "NOT_APPLICABLE",
        "span_m": [round(v, 6) for v in span],
        "nominal_loaded_mass_kg": meta["variant"]["nominal_total_mass_kg"],
        "image_nonuniform": True,
        "human_visual_review": "PENDING",
        "dual_avatar_grips": "NOT_TESTED",
        "commercial_approval": False,
    }
    meta["qa"]["roundtrip"] = "PASS"
    (folder / "asset.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (folder / "qa_report.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser.add_argument("--asset-dir", type=Path, required=True)
    parsed = parser.parse_args(args)
    print("EMS_BAR_QA=" + json.dumps(inspect(parsed.asset_dir.resolve())))
