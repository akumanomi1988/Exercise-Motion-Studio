"""Verify animated GLB contains actual changing transforms from a raw-pose preview.

Runs headless Blender against already exported diagnostic GLB, not humanoid QA.
"""
import argparse
import json
import sys
from pathlib import Path
import bpy

argp = argparse.ArgumentParser()
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
argp.add_argument("--asset-dir", type=Path, required=True)
args = argp.parse_args(argv)
folder = args.asset_dir.resolve(strict=True)
meta = json.loads((folder / "debug_manifest.json").read_text(encoding="utf-8"))
assert meta["commercial_approval"] is False
assert meta["avatar_model"] == "NONE"
assert meta["retarget"] == "NOT_DONE"
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(folder / "pose_debug.glb"))
objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert len(objects) >= 33, f"expected at least 33 animated landmark meshes, got {len(objects)}"
assert len(bpy.data.actions) > 0, "animated GLB has no actions"
scene = bpy.context.scene
end = max(2, scene.frame_end)
scene.frame_set(1)
first = {o.name: tuple(o.matrix_world.translation) for o in objects}
scene.frame_set(end)
last = {o.name: tuple(o.matrix_world.translation) for o in objects}
motion = sum(
    sum((a-b)**2 for a, b in zip(first[o.name], last[o.name]))
    for o in objects
)
assert motion > .0001, f"imported animation did not move between first and last frames: {motion}"
assert (folder / "pose_debug.png").stat().st_size > 1000
print("EMS_DEBUG_GLB_QA=" + json.dumps({
    "status": "TECHNICAL_PREVIEW_PASS",
    "mesh_count": len(objects),
    "actions_count": len(bpy.data.actions),
    "world_translation_displacement_sq": round(motion, 7),
    "commercial_approval": False,
    "humanoid_retarget": False,
    "biomechanics_qa": False,
}))
