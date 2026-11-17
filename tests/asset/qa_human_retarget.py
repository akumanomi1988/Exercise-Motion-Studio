"""Headless Blender proof of animated skin deformation in a REAL-video retarget.

Does NOT certify anatomical correctness, bone twist, rooting, contact or legal
distribution. On false-pass conditions stop and leave G1 IN_PROGRESS.
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


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for chunk in iter(lambda: inp.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require(ok, reason):
    if not ok:
        raise AssertionError(reason)


def skin_sample(mesh, rig, frame):
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    dep = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh.evaluated_get(dep)
    geo = evaluated.to_mesh()
    try:
        step = max(1, len(geo.vertices) // 400)
        return [
            tuple(mesh.matrix_world @ geo.vertices[i].co)
            for i in range(0, len(geo.vertices), step)
        ]
    finally:
        evaluated.to_mesh_clear()


def inspect(folder: Path):
    report = json.loads((folder / "retarget_manifest.json").read_text(
        encoding="utf-8"
    ))
    require(report["data_type"] == "SKINNED_HUMAN_RETARGET_DIAGNOSTIC_NOT_FINAL_MOTION",
            "not retarget output")
    require(report["method"] == "REAL_CAPTURE_SEGMENT_DIRECTION_RETARGET",
            "source provenance must be authentic video processing")
    require(report["commercial_approval"] is False and
            report["qa_gate_g1"] == "NOT_APPROVED",
            "unreviewed source cannot be approved by technical checks")
    require(report["source_video_license"] == "CC-BY-SA-4.0",
            "source license is missing")
    require(report["human_visual_review"] == "PENDING" and
            report["biomechanics_review"] == "PENDING",
            "cannot bypass human review")
    require(report["source_frames"] >= 3 and report["detected_frames"] >= 3,
            "not enough actual human samples")
    require(report["animated_bones"] >= 14,
            "no realistic coverage of major leg/arm bones")
    for name, checksum in report["file_sha256"].items():
        file = folder / name
        require(file.is_file() and file.stat().st_size > 100,
                "missing output " + name)
        require(sha(file) == checksum, "output modified since generation: " + name)
    require((folder / "retarget_review.png").stat().st_size > 10000,
            "render missing")
    image = bpy.data.images.load(str(folder / "retarget_review.png"),
                                 check_existing=False)
    require(tuple(image.size) == (512, 768), "wrong review preview size")
    sample_pixels = image.pixels
    count_colors = set()
    step = max(4, (len(sample_pixels) // 600 // 4) * 4)
    for i in range(0, len(sample_pixels) - 4, step):
        count_colors.add(tuple(round(float(v), 2)
                               for v in sample_pixels[i:i + 3]))
    require(len(count_colors) > 10, "blank/noninformative diagnostic image")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(folder / "retarget_review.glb"))
    rigs = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    require(len(rigs) == 1, "GLB roundtrip must preserve single humanoid rig")
    rig = rigs[0]
    require(len(rig.data.bones) == 53, "GLB bone hierarchy lost")
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"
              and len(o.data.vertices) >= 1000 and any(
                  m.type == "ARMATURE" and m.object == rig
                  for m in o.modifiers
              )]
    require(len(meshes) >= 1, "imported GLB has no skinned body")
    body = max(meshes, key=lambda m: len(m.data.vertices))
    require(sum(bool(v.groups) for v in body.data.vertices) >= 1000,
            "real vertex skin weights missing")
    require(len(bpy.data.actions) > 0,
            "GLB contains no actual animation actions")
    require(rig.animation_data is not None,
            "armature imported without bound action")

    # Evaluate REAL deformed vertices of the SKINNED MESH, not root translations
    # or static posebones alone. Any nonzero pose must alter surface geometry.
    first = skin_sample(body, rig, 1)
    max_mesh_displacement = 0.0
    last = report["timeline_end_frame"]
    for fno in sorted({1, max(2, last // 4),
                       max(2, last // 2), max(2, last * 3 // 4),
                       last}):
        other = skin_sample(body, rig, fno)
        require(len(first) == len(other), "body topology changed over time")
        delta = max((math.dist(a, b) for a, b in zip(first, other)),
                    default=0.0)
        max_mesh_displacement = max(max_mesh_displacement, delta)
    require(max_mesh_displacement > .008,
            f"animated GLB has no genuine skin motion: {max_mesh_displacement}")

    # Reopening the editable Blender project verifies it is more than a
    # glTF roundtrip. It must contain the actual rig with an action.
    bpy.ops.wm.open_mainfile(filepath=str(folder / "retarget_review.blend"))
    edits = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    require(len(edits) == 1 and
            edits[0].animation_data and edits[0].animation_data.action,
            "editable Blender source lost animated skin")
    result = {
        "technical_skinned_retarget": "PASS",
        "variant": report["variant"],
        "source_frames": report["source_frames"],
        "actual_detected_frames": report["detected_frames"],
        "mapped_bones": report["animated_bones"],
        "glb_bones": len(rig.data.bones),
        "glb_skin_weights": sum(bool(v.groups) for v in body.data.vertices),
        "real_mesh_deformation_span_m": round(max_mesh_displacement, 6),
        "human_visual_review": "PENDING",
        "biomechanics_review": "PENDING",
        "commercial_approval": False,
    }
    (folder / "retarget_qa.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print("EMS_REAL_SKINNED_GLB_QA=" + json.dumps(result))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args(args)
    inspect(a.output_dir.resolve(strict=True))
