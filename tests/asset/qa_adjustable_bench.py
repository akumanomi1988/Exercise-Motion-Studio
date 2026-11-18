"""Real Blender/GLB roundtrip QA for the procedural articulated bench.

Checks animated rigid components and telescope geometry at five actual frames.
Tests a TECHNICAL movement of the equipment, not a human exercise or safety load.
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

SAMPLES = (1, 13, 25, 37, 49)
PARTS = (
    "Moving backrest pad",
    "Telescoping casing L", "Telescoping rod L",
    "Telescoping casing R", "Telescoping rod R",
)
BACK_LENGTH = .92
HINGE = Vector((0.0, -.18, .50))


def require(check, message):
    if not check:
        raise AssertionError(message)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as reader:
        for part in iter(lambda: reader.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def support_endpoints(obj, base, tip):
    """Geometric cylinder endpoints in world coordinates, independent of
    how the glTF importer rebases local mesh axes or applies object transforms.

    This also screens for sideways displacement, not just axial extension.
    """
    axis = (tip - base).normalized()
    points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    projected = [(p - base).dot(axis) for p in points]
    radial = max(((point - base) - axis * longitudinal).length
                 for point, longitudinal in zip(points, projected))
    if radial > .032:
        print("EMS_BRACE_DIAGNOSTIC=" + json.dumps({
            "object": obj.name,
            "frame": bpy.context.scene.frame_current,
            "radial_error_m": radial,
            "base": list(base), "tip": list(tip),
            "object_world_location": list(obj.matrix_world.translation),
            "object_world_rotation": list(obj.matrix_world.to_quaternion()),
            "min_max_axis_m": [min(projected), max(projected)],
            "action": str(obj.animation_data.action.name)
                if obj.animation_data and obj.animation_data.action else None,
        }))
    require(radial <= .032, f"{obj.name}: support cylinder deviates from axis "
            f"by {radial:.5f}m at frame {bpy.context.scene.frame_current}")
    return (base + min(projected) * axis,
            base + max(projected) * axis)


def snapshot():
    scene = bpy.context.scene
    objects = bpy.data.objects
    require(all(name in objects and objects[name].type == "MESH"
                for name in PARTS), "animated equipment meshes missing")
    back = objects["Moving backrest pad"]
    angle_vec = back.matrix_world.to_3x3() @ Vector((0, 1, 0))
    angle = math.degrees(math.atan2(angle_vec.z, angle_vec.y))
    pivot = back.matrix_world @ Vector((0, 0, 0))
    require((pivot - HINGE).length < .008, "backrest hinge translated")
    require(-.5 <= angle <= 75.5, "backrest outside mechanical limits")
    for key, side in (("L", -.112), ("R", .112)):
        base = Vector((side, .08, .20))
        tip = Vector((side,
                      HINGE.y + .63 * math.cos(math.radians(angle)),
                      HINGE.z + .63 * math.sin(math.radians(angle))))
        casing = objects[f"Telescoping casing {key}"]
        rod = objects[f"Telescoping rod {key}"]
        casing_start, casing_end = support_endpoints(casing, base, tip)
        rod_start, rod_end = support_endpoints(rod, base, tip)
        require((casing_start - base).length < .025,
                f"{key}: casing detached from base")
        require((rod_end - tip).length < .025,
                f"{key}: telescoping rod detached from backrest; "
                f"measured={tuple(round(v,4) for v in rod_end)}, "
                f"expected={tuple(round(v,4) for v in tip)}")
        require((rod_start - (base + (tip-base).normalized() * .19)).length < .025,
                f"{key}: telescope rod jumps from casing")
        require((casing_end - base).length > .27 and
                (casing_end - base).length < .31,
                f"{key}: casing geometry is not a fixed-length cylinder")
    return {
        "angle": round(angle, 4),
        "hinge_world_m": [round(float(x), 5) for x in pivot],
        "backrest_tip_m": [
            round(float(x), 5) for x in
            (back.matrix_world @ Vector((0, BACK_LENGTH, 0)))
        ],
    }


def read_animation(label, angle_start, angle_peak):
    objects = bpy.data.objects
    require(all(name in objects for name in PARTS),
            f"{label}: missing articulated parts")
    require(len(bpy.data.actions) >= 1, f"{label}: no real animation")
    samples = {}
    for fno in SAMPLES:
        bpy.context.scene.frame_set(fno)
        bpy.context.view_layer.update()
        samples[fno] = snapshot()
    require(abs(samples[1]["angle"] - angle_start) <= .8,
            f"{label}: unexpected initial backrest angle: {samples[1]}")
    require(abs(samples[25]["angle"] - angle_peak) <= 1.0,
            f"{label}: mid-animation hinge angle incorrect: {samples[25]}")
    require(abs(samples[49]["angle"] - angle_start) <= .8,
            f"{label}: final pose did not return to initial angle")
    require(abs(samples[1]["angle"] - samples[25]["angle"]) >= 12,
            f"{label}: equipment does not actually articulate")
    require(math.dist(samples[1]["backrest_tip_m"],
                      samples[25]["backrest_tip_m"]) >= .12,
            f"{label}: visible backrest does not move")
    return samples


def inspect(root):
    manifest_file = root / "asset.json"
    meta = json.loads(manifest_file.read_text(encoding="utf-8"))
    require(meta.get("licenses", {}).get("status") == "PENDING",
            "commercial rights must not be claimed")
    require(meta["licenses"]["distribution_approved"] is False,
            "technical QA must not approve distribution")
    require(meta["qa"]["commercial_approval"] is False,
            "not a commercially approved bench")
    require(meta["kinematics"]["type"] == "articulated",
            "expected actual machine kinematics")
    joints = meta["kinematics"]["joints"]
    require(len(joints) == 1 and joints[0]["type"] == "revolute",
            "the real hinge is not declared")
    start = int(meta["variant"]["back_angle_degrees"])
    peak = int(meta["kinematics"]["preview_animation"]["peak_angle_degrees"])
    require(start in (0, 30, 45, 60, 75) and 0 <= peak <= 75,
            "invalid tested variant")
    for name, digest in meta["file_sha256"].items():
        path = root / name
        require(path.is_file() and path.stat().st_size > 1024 and
                sha(path) == digest, "missing or altered artifact: " + name)

    bpy.ops.wm.open_mainfile(filepath=str(root / "asset.blend"))
    source_parts = [o for o in bpy.data.objects if o.get("ems_export")]
    require(len(source_parts) == 19, "source bench has missing procedural parts")
    require(len({o.name for o in source_parts}) == len(source_parts),
            "duplicate equipment part names")
    source = read_animation(".blend", start, peak)
    blender_version = bpy.app.version_string

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(root / "asset.glb"))
    imported_meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    require(len(imported_meshes) == len(source_parts),
            "GLB lost meshes or accidentally contains studio objects")
    require(len([o for o in imported_meshes if len(o.data.materials)])
            == len(imported_meshes), "GLB lost original materials")
    glb = read_animation("GLB reimport", start, peak)
    for fno in SAMPLES:
        require(abs(source[fno]["angle"] - glb[fno]["angle"]) < .6,
                "glTF lost a real backrest hinge transform")
        require(math.dist(source[fno]["backrest_tip_m"],
                          glb[fno]["backrest_tip_m"]) < .02,
                "glTF altered moving bench geometry")

    image = bpy.data.images.load(str(root / "preview.png"), check_existing=False)
    require(tuple(image.size) == (768, 512), "preview dimensions wrong")
    colors = set()
    values = image.pixels
    step = max(4, (len(values) // 1000 // 4) * 4)
    for idx in range(0, len(values) - 4, step):
        colors.add(tuple(round(float(c), 2) for c in values[idx:idx + 3]))
    require(len(colors) > 15, "preview is blank or uninformative")

    report = {
        "status": "TECHNICAL_KINEMATICS_AND_GLB_ROUNDTRIP_PASS",
        "asset_id": meta["asset_id"],
        "blender_version": blender_version,
        "source_mesh_count": len(source_parts),
        "glb_mesh_count": len(imported_meshes),
        "source_actual_frames": source,
        "glb_actual_frames": glb,
        "max_backrest_angle_roundtrip_error_degrees": round(
            max(abs(source[f]["angle"] - glb[f]["angle"]) for f in SAMPLES), 4),
        "maximum_backrest_tip_roundtrip_error_m": round(
            max(math.dist(source[f]["backrest_tip_m"],
                          glb[f]["backrest_tip_m"]) for f in SAMPLES), 6),
        "kinematic_bounds_status": "PASS",
        "telescoping_support_endpoints": "PASS",
        "human_contact_with_both_avatars": "NOT_TESTED",
        "structural_load_rating": "NOT_CERTIFIED",
        "human_visual_review": "PENDING",
        "commercial_approval": False,
    }
    meta["qa"]["roundtrip"] = "PASS"
    (root / "qa_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest_file.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--asset-dir", type=Path, required=True)
    args = p.parse_args(argv)
    report = inspect(args.asset_dir.resolve(strict=True))
    print("EMS_BENCH_QA=" + json.dumps({
        "asset_id": report["asset_id"],
        "source_mesh_count": report["source_mesh_count"],
        "angle_roundtrip_error_degrees":
            report["max_backrest_angle_roundtrip_error_degrees"],
        "commercial_approval": False,
    }))
