"""AG1 technical validation of REAL MakeHuman exported skinned body/rig.

Tests real GLB import, bone weights, material, .blend reopen and deformation.
No avatar animation is claimed; final human appearance/IK remain PENDING.
"""
import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

import bpy


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _find_skin_and_rig():
    rigs = [x for x in bpy.context.scene.objects if x.type == "ARMATURE"]
    if not rigs:
        raise AssertionError("no exported armature")
    meshes = [
        m for m in bpy.context.scene.objects if m.type == "MESH"
        and any(mod.type == "ARMATURE" for mod in m.modifiers)
        and len(m.data.vertices) >= 1000
    ]
    if not meshes:
        raise AssertionError("no weighted, skinned body mesh imported")
    mesh = max(meshes, key=lambda m: len(m.data.vertices))
    modifier = next(mod for mod in mesh.modifiers
                    if mod.type == "ARMATURE" and mod.object is not None)
    rig = modifier.object
    if rig.type != "ARMATURE":
        raise AssertionError("invalid skin armature binding")
    return mesh, rig


def validate(path: Path):
    meta = json.loads((path / "asset.json").read_text(encoding="utf-8"))
    assert meta["source"]["upstream_commit"] == "9de0707fdc88438d7c53a1a2ac7937d9221e2431"
    assert meta["source"]["assets_license"] == "CC0-1.0"
    assert meta["source"]["external_asset_packs_used"] is False
    assert meta["licenses"]["status"] == "PENDING"
    assert meta["licenses"]["distribution_approved"] is False
    assert meta["rig"]["animation"] == "NOT_PRESENT"
    assert meta["qa"]["commercial_approval"] is False
    for name in ("asset.glb", "asset.blend", "preview.png"):
        resource = path / name
        assert resource.stat().st_size > 10_000
        assert _sha(resource) == meta["file_sha256"][name]

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(path / "asset.glb"))
    imported_mesh, imported_rig = _find_skin_and_rig()
    assert len(imported_mesh.data.vertices) > 1000
    assert len(imported_rig.data.bones) >= 20
    assert len(imported_mesh.vertex_groups) >= 20
    assert any(slot.material for slot in imported_mesh.material_slots)
    glb_count = sum(any(g.weight > 0 for g in vertex.groups)
                    for vertex in imported_mesh.data.vertices)
    assert glb_count > 1000
    dims = meta["dimensions_m"]
    assert 1.3 < dims["height_z"] < 2.5

    # Opening the EDITABLE source is a separate roundtrip test.
    bpy.ops.wm.open_mainfile(filepath=str(path / "asset.blend"))
    body, rig = _find_skin_and_rig()
    counts = Counter()
    for v in body.data.vertices:
        for g in v.groups:
            if g.weight > 1e-5:
                counts[body.vertex_groups[g.group].name] += 1
    # Choose a genuinely skinned non-root deform bone, not an arbitrary name.
    candidates = [
        (counts.get(b.name, 0), b.name)
        for b in rig.pose.bones
        if b.parent is not None and counts.get(b.name, 0) > 200
    ]
    assert candidates, "no bone with enough skin weights to test deformation"
    candidates.sort(reverse=True)
    selected_name = candidates[0][1]
    pose_bone = rig.pose.bones[selected_name]
    dg = bpy.context.evaluated_depsgraph_get()
    bpy.context.view_layer.update()

    def sampled_positions():
        evaluated = body.evaluated_get(dg)
        evaluated_mesh = evaluated.to_mesh()
        try:
            return [tuple(v.co) for v in evaluated_mesh.vertices]
        finally:
            evaluated.to_mesh_clear()

    before = sampled_positions()
    pose_bone.rotation_mode = "XYZ"
    pose_bone.rotation_euler[0] += 0.25
    bpy.context.view_layer.update()
    after = sampled_positions()
    assert len(before) == len(after)
    max_displacement = max(
        math.dist(p, q) for p, q in zip(before, after)
    )
    assert max_displacement > 0.002, (
        f"armature did not actually deform the body mesh: {max_displacement}"
    )

    report = {
        "technical_rig_roundtrip": "PASS",
        "asset_id": meta["asset_id"],
        "variant": meta["variant"],
        "glb_bones": len(imported_rig.data.bones),
        "glb_skinned_vertices": glb_count,
        "original_bones": len(rig.data.bones),
        "original_vertices": len(body.data.vertices),
        "deformation_test_bone": selected_name,
        "deformation_max_distance_m": round(max_displacement, 6),
        "commercial_approval": False,
        "retarget_from_video": "NOT_TESTED",
        "human_visual_review": "PENDING",
    }
    (path / "qa_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print("EMS_MPFb_AVATAR_QA=" + json.dumps(report))


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    a.add_argument("--asset-dir", required=True, type=Path)
    opts = a.parse_args(args)
    validate(opts.asset_dir.resolve(strict=True))
