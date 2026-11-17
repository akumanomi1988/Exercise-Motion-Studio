"""Generate actual MakeHuman/MPFB skinned adult bodies with the same GameEngine rig.

Uses pinned EXTERNAL MPFB source as a Blender authoring dependency. Its core
assets/rig/weights are CC0; the addon source is GPL, never embedded in GLB.
No third-party asset packs. This step does not capture motion or validate
commercial appearance; human visual review and G1 remain pending.

Run only within Blender 4.2+ with the MPFB source already available locally:
  blender -b --python src/blender/build_mpfb_avatars.py -- \
    --addon-parent data/tools/mpfb2-<commit>/src --output-dir data/avatars/male \
    --variant male
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

MPFB_COMMIT = "9de0707fdc88438d7c53a1a2ac7937d9221e2431"
MPFB_REPO = "https://github.com/makehumancommunity/mpfb2"
RIG_NAME = "game_engine"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _addon(addon_parent: Path):
    package = addon_parent / "mpfb"
    if not (package / "blender_manifest.toml").is_file():
        raise RuntimeError("Pinned MPFB source manifest missing")
    import addon_utils
    import importlib
    module_name = "bl_ext.user_default.mpfb"
    if module_name not in bpy.context.preferences.addons:
        addon_utils.enable(module_name, default_set=False, persistent=False)
    if module_name not in bpy.context.preferences.addons:
        raise RuntimeError("MPFB Blender extension was not enabled")
    # Blender 4.2+ Extensions must be imported through their registered
    # bl_ext namespace so bpy.utils.extension_path_user works correctly.
    HumanService = importlib.import_module(
        module_name + ".services.humanservice"
    ).HumanService
    TargetService = importlib.import_module(
        module_name + ".services.targetservice"
    ).TargetService
    Properties = importlib.import_module(
        module_name + ".entities.objectproperties"
    ).HumanObjectProperties
    return HumanService, TargetService, Properties


def _material(name, color, roughness=.65):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    m.diffuse_color = (*color, 1)
    return m


def _evaluated_geometry_hash(mesh):
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh.evaluated_get(depsgraph)
    data = evaluated.to_mesh()
    try:
        hasher = hashlib.sha256()
        for vertex in data.vertices:
            hasher.update(struct.pack(
                "<3f", float(vertex.co.x), float(vertex.co.y),
                float(vertex.co.z)
            ))
        return hasher.hexdigest()
    finally:
        evaluated.to_mesh_clear()


def _outfit_surface(mesh, variant):
    """Original sportswear-colored surface regions, NOT a clothing mesh/fit.

    A technical and modest preview material assignment that does not alter the
    MakeHuman CC0 base topology/weights. Final commercial clothing is pending.
    """
    base = _material("Warm neutral anatomy preview", (.54, .40, .32), .82)
    shirt = _material("Training top navy", (.032, .095, .17), .57)
    shorts = _material("Training shorts graphite", (.085, .105, .125), .72)
    mesh.data.materials.clear()
    for material in (base, shirt, shorts):
        mesh.data.materials.append(material)
    verts = [v.co for v in mesh.data.vertices]
    minz, maxz = min(v.z for v in verts), max(v.z for v in verts)
    height = maxz - minz
    if height <= 1:
        raise RuntimeError("MakeHuman base mesh has implausible height/scale")
    bpy.context.view_layer.update()
    for poly in mesh.data.polygons:
        centroid = sum((verts[i].z for i in poly.vertices), 0.) / len(poly.vertices)
        cx = sum((verts[i].x for i in poly.vertices), 0.) / len(poly.vertices)
        relative_z = (centroid - minz) / height
        if .57 <= relative_z <= .82 and abs(cx) < .23 * height:
            poly.material_index = 1
        elif .38 <= relative_z < .57 and abs(cx) < .18 * height:
            poly.material_index = 2
        else:
            poly.material_index = 0
        poly.use_smooth = True
    return height


def _camera_and_lights(height):
    bpy.ops.object.camera_add(location=(1.8, -3.0, height * .58))
    cam = bpy.context.object
    cam.name = "Studio Preview Camera — not distributed"
    direction = Vector((0, 0, height * .51)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = height * 1.37
    bpy.context.scene.camera = cam
    for name, loc, energy in (
        ("Key", (1.4, -1.8, height * 1.4), 650),
        ("Fill", (-1.5, -.5, height * .85), 350),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = f"Preview {name} light — not distributed"
        lamp.data.energy = energy
        lamp.data.size = 3
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 8
    if hasattr(scene.cycles, "use_denoising"):
        scene.cycles.use_denoising = False
    for layer in scene.view_layers:
        if hasattr(layer, "cycles") and hasattr(layer.cycles, "use_denoising"):
            layer.cycles.use_denoising = False
    scene.render.resolution_x = 512
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (.07, .075, .085)


def generate(addon_parent: Path, output: Path, variant: str):
    if variant not in ("male", "female"):
        raise ValueError("variant must be male or female")
    HumanService, TargetService, Properties = _addon(addon_parent)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    basemesh = HumanService.create_human(
        mask_helpers=True, detailed_helpers=False,
        extra_vertex_groups=True, feet_on_ground=True, scale=.1
    )
    if basemesh is None or basemesh.type != "MESH":
        raise RuntimeError("MPFB did not generate an actual human mesh")
    Properties.set_value(
        "gender", 1.0 if variant == "male" else 0.0,
        entity_reference=basemesh
    )
    TargetService.reapply_macro_details(basemesh)
    body_geometry_hash = _evaluated_geometry_hash(basemesh)
    # Both variants use identical GAME_ENGINE semantic bones and weight pack.
    rig = HumanService.add_builtin_rig(
        basemesh, RIG_NAME, import_weights=True
    )
    if rig is None or rig.type != "ARMATURE":
        raise RuntimeError("MPFB game-engine armature generation failed")
    if not any(m.type == "ARMATURE" and m.object == rig for m in basemesh.modifiers):
        raise RuntimeError("MPFB did not bind the mesh to the armature")
    skinned = sum(
        any(group.weight > 1e-6 for group in v.groups)
        for v in basemesh.data.vertices
    )
    if skinned < 1000:
        raise RuntimeError("MPFB mesh does not have enough weighted vertices")
    bone_map = {
        bone.name: bone.parent.name if bone.parent else None
        for bone in rig.data.bones
    }
    if len(bone_map) < 20:
        raise RuntimeError("MPFB game-engine rig has too few bones")
    basemesh.name = f"EMS {variant} adult skinned CC0 base"
    rig.name = f"EMS {variant} canonical game-engine rig"
    actual_height = _outfit_surface(basemesh, variant)
    _camera_and_lights(actual_height)
    output.mkdir(parents=True, exist_ok=True)

    blend = output / "asset.blend"
    glb = output / "asset.glb"
    png = output / "preview.png"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.object.select_all(action="DESELECT")
    basemesh.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(
        filepath=str(glb), export_format="GLB",
        use_selection=True, export_skins=True, export_animations=False,
        export_cameras=False, export_lights=False,
    )
    if not glb.is_file() or glb.stat().st_size < 100_000:
        raise RuntimeError("Skinned humanoid GLB export missing or too small")

    bpy.context.scene.render.filepath = str(png)
    bpy.ops.render.render(write_still=True)
    if not png.is_file() or png.stat().st_size < 10_000:
        raise RuntimeError("Humanoid preview missing")

    # Dimensions in Blender's original Z-up meters. GLB is converted by
    # glTF exporter to Y-up; no implicit avatar calibration/retarget.
    from mathutils import Vector as V
    corners = [basemesh.matrix_world @ V(c)
               for c in basemesh.bound_box]
    xyz_min = [min(c[i] for c in corners) for i in range(3)]
    xyz_max = [max(c[i] for c in corners) for i in range(3)]
    extents = [round(xyz_max[i] - xyz_min[i], 6) for i in range(3)]

    body_meta = {
        "schema_version": "1.0",
        "asset_id": f"ems.avatar.human.adult.{variant}.v1",
        "version": "0.1.0",
        "category": "avatar",
        "subcategory": "rigged_human",
        "variant": variant,
        "mpfb_gender_macro_value": 1.0 if variant == "male" else 0.0,
        "gender_mapping_reference": "src/mpfb/data/targets/macrodetails/macro.json",
        "unit": "meter",
        "coordinate_system": "Blender Z-up; glTF export Y-up",
        "dimensions_m": {
            "length_x": extents[0], "width_y": extents[1],
            "height_z": extents[2],
        },
        "models": {
            "editable": "asset.blend", "distribution": "asset.glb",
            "thumbnail": "preview.png",
        },
        "rig": {
            "type": "MPFB_GAME_ENGINE",
            "profile_id": "ems.mpfb.game_engine.v1",
            "bones": bone_map,
            "bone_count": len(bone_map),
            "base_vertex_count": len(basemesh.data.vertices),
            "evaluated_mesh_sha256": body_geometry_hash,
            "weighted_vertices": skinned,
            "material_scheme": "TECHNICAL_TRAINING_GARMENT_SURFACES_NOT_REAL_CLOTH",
            "animation": "NOT_PRESENT",
            "retarget": "NOT_VERIFIED",
        },
        "grip_points": [],
        "attachment_points": [],
        "contact_surfaces": [],
        "collision_shapes": [],
        "source": {
            "kind": "VERIFIED_THIRD_PARTY",
            "upstream_repo": MPFB_REPO,
            "upstream_commit": MPFB_COMMIT,
            "assets_license": "CC0-1.0",
            "addon_code_license": "GPL-3.0-or-later",
            "addon_embedded_in_output": False,
            "external_asset_packs_used": False,
            "authoring_environment": bpy.app.version_string,
        },
        "licenses": {
            "status": "PENDING",
            "distribution_approved": False,
            "reviewer": None,
            "source_url": f"{MPFB_REPO}/blob/{MPFB_COMMIT}/LICENSE.md",
            "commercial_use_candidate": True,
            "attribution": "CC0 core",
        },
        "qa": {
            "rig_skinning_built": True,
            "glb_roundtrip": "NOT_TESTED",
            "human_visual_review": "PENDING",
            "animation_compatibility": "NOT_TESTED",
            "commercial_approval": False,
        },
        "file_sha256": {p.name: _sha(p) for p in (blend, glb, png)},
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "asset.json").write_text(
        json.dumps(body_meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("EMS_MPFb_HUMAN_MODEL=" + json.dumps({
        "variant": variant, "vertices": len(basemesh.data.vertices),
        "weighted_vertices": skinned, "bone_count": len(bone_map),
        "height_m": extents[2],
        "model_glb_bytes": glb.stat().st_size,
        "evaluated_mesh_sha256": body_geometry_hash,
        "commercial_approval": False,
    }))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser.add_argument("--addon-parent", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--variant", required=True, choices=("male", "female"))
    args = parser.parse_args(argv)
    generate(args.addon_parent.resolve(strict=True), args.output_dir.resolve(),
             args.variant)
