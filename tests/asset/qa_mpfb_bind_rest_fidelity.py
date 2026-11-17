"""Fail closed if exported MPFB GLB distorts the ORIGINAL .blend rest mesh.

Test actual evaluated skinned-body world coordinates, NOT merely vertex counts,
bone counts, presence of skin weights or existence of an armature. A GLB with
correct weights but wrong inverse-bind transforms must fail. Blender headless.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree


def actual_mesh():
    rigs = [obj for obj in bpy.context.scene.objects
            if obj.type == "ARMATURE"]
    assert len(rigs) == 1, "expect one MPFB rig"
    rig = rigs[0]
    skins = [
        obj for obj in bpy.context.scene.objects
        if obj.type == "MESH" and obj.data and
        len(obj.data.vertices) >= 1000 and any(
            mod.type == "ARMATURE" and mod.object == rig for mod in obj.modifiers
        )
    ]
    assert skins, "no real skinned body found"
    mesh = max(skins, key=lambda m: len(m.data.vertices))
    return rig, mesh


def evaluated_world_vertices(mesh):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    obj = mesh.evaluated_get(dg)
    data = obj.to_mesh()
    try:
        return [mesh.matrix_world @ vert.co for vert in data.vertices]
    finally:
        obj.to_mesh_clear()


def inspect(folder):
    asset = json.loads((folder / "asset.json").read_text(encoding="utf-8"))
    assert asset["rig"]["profile_id"] == "ems.mpfb.game_engine.v1"
    assert asset["licenses"]["distribution_approved"] is False
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # The editable source is the canonical undistorted MakeHuman mesh.
    bpy.ops.wm.open_mainfile(filepath=str(folder / "asset.blend"))
    original_rig, original_mesh = actual_mesh()
    original = evaluated_world_vertices(original_mesh)
    original_rig_matrix = [list(row) for row in original_rig.matrix_world]
    original_mesh_matrix = [list(row) for row in original_mesh.matrix_world]

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(folder / "asset.glb"))
    imported_rig, imported_mesh = actual_mesh()
    imported = evaluated_world_vertices(imported_mesh)
    imported_rig_matrix = [list(row) for row in imported_rig.matrix_world]
    imported_mesh_matrix = [list(row) for row in imported_mesh.matrix_world]
    assert len(original) > 10_000 and len(imported) > 10_000
    assert all(math.isfinite(a) for v in imported for a in v)

    kd = KDTree(len(original))
    for i, p in enumerate(original):
        kd.insert(p, i)
    kd.balance()
    # glTF splits vertices by material/normal, so compare nearest world-space
    # geometry, NOT identical vertex IDs or counts.
    distances = sorted(kd.find(pt)[2] for pt in imported)
    p95 = distances[int(.95 * (len(distances) - 1))]
    p99 = distances[int(.99 * (len(distances) - 1))]
    maximum = distances[-1]
    mean = statistics.mean(distances)
    result = {
        "variant": asset["variant"],
        "original_vertices": len(original),
        "imported_vertices": len(imported),
        "mean_nearest_rest_position_deviation_m": round(mean, 7),
        "p95_deviation_m": round(p95, 7),
        "p99_deviation_m": round(p99, 7),
        "max_deviation_m": round(maximum, 7),
        "original_rig_matrix_world": original_rig_matrix,
        "original_mesh_matrix_world": original_mesh_matrix,
        "glb_rig_matrix_world": imported_rig_matrix,
        "glb_mesh_matrix_world": imported_mesh_matrix,
        "technical_approval": p95 < .010 and p99 < .020 and maximum < .050,
        "human_visual_review": "PENDING",
        "commercial_approval": False,
    }
    (folder / "glb_rest_fidelity.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print("EMS_MPFb_GLB_BIND_REST_FIDELITY=" + json.dumps(result))
    assert result["technical_approval"], (
        "GLB rest-body differs from .blend source. Animation and 53 bones "
        "are insufficient. Inspect object transforms/inverse bind and skin "
        f"geometry. p95 {p95:.4f} m, max {maximum:.4f} m"
    )
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p.add_argument("--avatar-dir", type=Path, required=True)
    a = p.parse_args(args)
    inspect(a.avatar_dir.resolve(strict=True))
