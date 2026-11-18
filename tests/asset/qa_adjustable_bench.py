"""Actual Blender GLB roundtrip and articulation QA for procedural bench.

Checks geometry/animation, not avatar contact, safety certification or human
visual approval. An unapproved asset must remain blocked for commercial export.
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

PIVOT = "Backrest hinge"
BACK = "Backrest padded surface"
SEAT = "Fixed seat padded surface"
FRAME = "Fixed center spine"


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise AssertionError(message)


def find(name, obj_type=None):
    found = [o for o in bpy.context.scene.objects
             if o.name == name or o.name.startswith(name + ".")]
    if obj_type:
        found = [o for o in found if o.type == obj_type]
    require(len(found) == 1, f"missing/duplicate {name} ({obj_type}): {len(found)}")
    return found[0]


def position(obj, frame):
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    return obj.matrix_world.translation.copy()


def validate(folder: Path):
    meta = json.loads((folder / "asset.json").read_text(encoding="utf-8"))
    require(meta["asset_id"] == "ems.equipment.bench.adjustable.v1", "wrong asset id")
    require(meta["licenses"]["status"] == "PENDING", "rights gate bypass")
    require(meta["licenses"]["distribution_approved"] is False,
            "bench cannot be commercially approved by technical QA")
    joints = meta["kinematics"]["joints"]
    require(len(joints) == 1 and joints[0]["type"] == "revolute", "missing revolute joint")
    joint = joints[0]
    require(joint["min_degrees"] == 0 and joint["max_degrees"] == 60,
            "unexpected hinge safety limits")
    require(joint["axis"] == [0, -1, 0], "hinge axis mismatch")
    require(joint["keyframes"] == [
        {"frame": 1, "angle_degrees": 0.0},
        {"frame": 16, "angle_degrees": 30.0},
        {"frame": 31, "angle_degrees": 60.0},
    ], "non-deterministic bench joint animation")
    for role in ("editable", "distribution", "thumbnail"):
        path = folder / meta["models"][role]
        require(path.is_file() and path.stat().st_size > 1024,
                f"missing authored output: {path.name}")
        require(sha(path) == meta["file_sha256"][path.name],
                f"tampered authored output: {path.name}")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(folder / "asset.glb"))
    objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    require(len(objects) >= 11, "GLB lost original bench geometry")
    require(all(len(o.material_slots) for o in objects),
            "missing glTF material on bench geometry")
    require(all(math.isfinite(v)
                for o in objects for p in o.data.vertices for v in
                (o.matrix_world @ p.co)), "nonfinite mesh geometry")
    hinge = find(PIVOT)
    back = find(BACK, "MESH")
    seat = find(SEAT, "MESH")
    fixed = find(FRAME, "MESH")
    require(back.parent == hinge, "GLB hinge-to-backrest hierarchy lost")

    # glTF stores animation timestamps in *seconds*. A fresh Blender importer
    # can use 24fps even though the source scene authored at 15fps. Sampling
    # imported frame 31 would evaluate only 1.25 seconds of a 2-second clip.
    # Verify identical physical instants, not identical frame indices.
    source_fps = meta["kinematics"]["timeline_fps"]
    source_duration = meta["kinematics"]["timeline_duration_seconds"]
    require(source_fps == 15 and source_duration == 2.0,
            "unexpected authored articulation timebase")
    imported_fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    start_frame = 1
    end_frame = 1 + round(source_duration * imported_fps)
    start_back = position(back, start_frame)
    end_back = position(back, end_frame)
    start_fixed = position(fixed, start_frame)
    end_fixed = position(fixed, end_frame)
    start_seat = position(seat, start_frame)
    end_seat = position(seat, end_frame)
    change = end_back - start_back
    # Geometric expected center displacement for radius 0.365m, 60 degrees:
    # dz = 0.365*sin(60) = 0.3161m; dx = 0.365*(cos(60)-1) = -0.1825m.
    expected_z = .365 * math.sin(math.radians(60))
    expected_x = .365 * (math.cos(math.radians(60)) - 1)
    require(abs(change.z - expected_z) < .025,
            f"backrest vertical travel does not match 60-degree hinge: {change.z:.5f} m")
    require(abs(change.x - expected_x) < .025,
            f"backrest longitudinal travel does not match hinge: {change.x:.5f} m")
    require((end_fixed - start_fixed).length < .001,
            "fixed frame must never move with backrest")
    require((end_seat - start_seat).length < .001,
            "fixed seat must not move with backrest")
    bpy.context.scene.frame_set(start_frame)
    bpy.context.view_layer.update()
    rot_start = hinge.matrix_world.to_quaternion().copy()
    bpy.context.scene.frame_set(end_frame)
    bpy.context.view_layer.update()
    rot_end = hinge.matrix_world.to_quaternion().copy()
    angle = math.degrees(rot_start.rotation_difference(rot_end).angle)
    require(abs(angle - 60.0) < 1.5,
            f"imported GLB rotation must retain real 60-degree movement: {angle}")
    require(hinge.animation_data and hinge.animation_data.action,
            "animated glTF hinge lost its bound action")

    png = bpy.data.images.load(str(folder / "preview.png"), check_existing=False)
    require(tuple(png.size) == (720, 540), "preview dimensions wrong")
    samples = png.pixels
    stride = max(4, (len(samples) // 1500 // 4) * 4)
    colors = {tuple(round(float(v), 2) for v in samples[i:i+3])
              for i in range(0, len(samples) - 3, stride)}
    require(len(colors) > 10, "preview is blank or visually uninformative")

    glb_mesh_count = len(objects)
    bpy.ops.wm.open_mainfile(filepath=str(folder / "asset.blend"))
    source_hinge = find(PIVOT)
    source_back = find(BACK, "MESH")
    require(source_hinge.animation_data and source_hinge.animation_data.action,
            "editable .blend missing actual backrest keyframes")
    require(source_back.parent == source_hinge,
            "editable .blend backrest no longer parented to articulation")

    report = {
        "technical_roundtrip": "PASS",
        "revolute_animation": "PASS",
        "glb_meshes": glb_mesh_count,
        "glb_backrest_vertical_travel_m": round(change.z, 6),
        "glb_backrest_horizontal_travel_m": round(change.x, 6),
        "glb_hinge_rotation_degrees": round(angle, 4),
        "imported_fps": imported_fps,
        "imported_end_frame_at_2_seconds": end_frame,
        "static_frame_invariant": "PASS",
        "static_seat_invariant": "PASS",
        "preview_resolution": [720, 540],
        "human_visual_review": "PENDING",
        "avatar_contact": "NOT_TESTED",
        "bench_collision": "NOT_TESTED",
        "commercial_approval": False,
    }
    meta["qa"]["joint_animation"] = "PASS"
    meta["qa"]["roundtrip"] = "PASS"
    (folder / "asset.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (folder / "qa_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print("EMS_ADJUSTABLE_BENCH_QA=" + json.dumps(report))
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p.add_argument("--asset-dir", type=Path, required=True)
    opts = p.parse_args(args)
    validate(opts.asset_dir.resolve(strict=True))
