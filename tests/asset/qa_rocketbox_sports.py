"""Headless QA of genuine Rocketbox skinned GLB; not exercise/IK approval."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def skinned_vertices(mesh):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh.evaluated_get(depsgraph)
    data = evaluated.to_mesh()
    try:
        stride = max(1, len(data.vertices) // 512)
        return [tuple(mesh.matrix_world @ data.vertices[i].co)
                for i in range(0, len(data.vertices), stride)]
    finally:
        evaluated.to_mesh_clear()


def inspect(source: Path, out: Path):
    src = json.loads((source / "source_provenance.json").read_text())
    report = json.loads((out / "import_report.json").read_text())
    require(src["license_spdx"] == report["license"] == "MIT",
            "third party source licence changed")
    require(not report["commercial_asset_approval"]
            and report["human_visual_approval"] == "PENDING",
            "no automated commercial approval permitted")
    for name, key in (("source.blend", "editable_blend_sha256"),
                      ("avatar.glb", "exported_glb_sha256"),
                      ("rest_review.png", "preview_png_sha256")):
        path = out / name
        require(path.is_file() and digest(path) == report[key],
                f"missing or altered real binary {name}")
    img = bpy.data.images.load(str(out / "rest_review.png"))
    require(tuple(img.size) == (512, 768),
            "real Blender review image has wrong dimensions")
    values = img.pixels
    stride = max(4, (len(values) // 400 // 4) * 4)
    require(len({tuple(round(float(v), 2) for v in values[i:i+3])
                 for i in range(0, len(values)-4, stride)}) >= 20,
            "avatar review image blank/uninformative")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(out / "avatar.glb"))
    rigs = [x for x in bpy.context.scene.objects if x.type == "ARMATURE"]
    mesh = [x for x in bpy.context.scene.objects if x.type == "MESH" and
            len(x.data.vertices) > 1000 and any(
                mod.type == "ARMATURE" and mod.object in rigs
                for mod in x.modifiers)]
    require(rigs and mesh, "GLB lost real armature or deforming meshes")
    rig = max(rigs, key=lambda o: len(o.data.bones))
    require(len(rig.data.bones) >= 25, "GLB lost humanoid skeleton bones")
    require(any(m.data.materials for m in mesh),
            "GLB has no attached source materials")
    images = [i for i in bpy.data.images if i.has_data and i.size[0] >= 1000]
    require(images, "GLB lost real source texture maps")
    body = max(mesh, key=lambda m: len(m.data.vertices))
    weights = sum(bool(v.groups) for v in body.data.vertices)
    require(weights > 1000, "GLB contains no usable skin weights")
    before = skinned_vertices(body)
    candidates = [b for b in rig.pose.bones if
                  ("arm" in b.name.lower() or "elbow" in b.name.lower())
                  and b.bone.use_deform]
    require(candidates, "no deforming arm bone for actual skinned motion test")
    chosen = max(candidates, key=lambda b: b.bone.length)
    chosen.rotation_mode = "QUATERNION"
    chosen.rotation_quaternion = Quaternion((0, 0, 1), .35)
    bpy.context.view_layer.update()
    after = skinned_vertices(body)
    require(len(before) == len(after), "animated skin sample sizes differ")
    deformation = max(math.dist(a, b) for a, b in zip(before, after))
    require(deformation > .002, "GLB skin does not actually deform under arm motion")
    require(math.isfinite(deformation) and deformation < 1.5,
            "unbounded skin deformation under simple bone movement")
    result = {
        "technical_glb_skeleton_and_skinning": "PASS",
        "variant": report["variant"],
        "source_avatar": report["source_avatar"],
        "bones": len(rig.data.bones),
        "skinned_body_weighted_vertices": weights,
        "actual_deforming_bone": chosen.name,
        "actual_mesh_deformation_under_20deg_arm_swing_m": round(deformation, 6),
        "embedded_source_texture_count": len(images),
        "rest_png": "VISUAL_REVIEW_REQUIRED",
        "exercise_retarged_real_video": "NOT_TESTED",
        "contact_and_hand_ik": "NOT_TESTED",
        "commercial_approval": False,
    }
    (out / "qa_report.json").write_text(json.dumps(result, indent=2)+"\n")
    print("EMS_ROCKETBOX_GLTF_QA=" + json.dumps(result))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--source-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args(argv)
    inspect(a.source_dir.resolve(strict=True), a.output_dir.resolve(strict=True))
