"""Original procedural hex dumbbell. Run with Blender in background mode.

blender -b --python src/blender/generate_hex_dumbbell.py -- --output-dir data/generated_assets/hex-10kg --mass-kg 10

Output is a REAL editable .blend, animated-scene-compatible GLB geometry and PNG.
This is one equipment asset, NOT an avatar, machine, exercise animation or
commercially approved model. Human visual and rights review remain mandatory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

ASSET_FAMILY = "ems.equipment.dumbbell.hex"
SOURCE_FILE = Path(__file__).resolve()


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _material(name: str, rgb: tuple[float, float, float],
              metallic: float, roughness: float) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        raise RuntimeError("Blender Principled BSDF node not available")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = (*rgb, 1.0)
    return mat


def _cylinder(name: str, radius: float, depth: float, x: float,
              segments: int, bevel: float, material: bpy.types.Material):
    # Blender cylinders default to local +Z, while this asset is aligned +X.
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=segments, radius=radius, depth=depth,
        end_fill_type="NGON", location=(x, 0, 0),
        rotation=(0, math.pi / 2, 0),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("Machined edge bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj["ems_export"] = True
    obj["asset_family"] = ASSET_FAMILY
    return obj


def _aim_camera(location: tuple[float, float, float]) -> None:
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.object
    camera.name = "Preview Camera (excluded from GLB)"
    direction = Vector((0, 0, 0)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 0.72
    bpy.context.scene.camera = camera


def _studio_lighting(radius: float) -> None:
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, -radius - 0.002))
    floor = bpy.context.object
    floor.name = "Studio floor (excluded from GLB)"
    floor.data.materials.append(_material("Studio matte grey", (.17, .18, .20), 0, .95))
    for name, loc, power, size in [
        ("Key", (0.8, -0.9, 1.4), 450, 1.6),
        ("Fill", (-0.5, 0.7, 0.8), 250, 1.2),
    ]:
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = f"Preview {name} (excluded from GLB)"
        lamp.data.energy = power
        lamp.data.shape = "DISK"
        lamp.data.size = size


def generate(output: Path, mass_kg: float) -> dict:
    if not math.isfinite(mass_kg) or not (2 <= mass_kg <= 30):
        raise ValueError("mass-kg must be finite and between 2 and 30")
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Dimensions are approximate family variants, not calibrated mass/physics.
    head_radius = 0.06 + 0.0025 * mass_kg
    head_length = 0.055 + 0.002 * mass_kg
    center_distance = 0.16 + head_length / 2
    shaft_length = 0.34
    shaft_radius = 0.016
    outer_length = 2 * center_distance + head_length

    rubber = _material("Original charcoal rubber", (.035, .039, .045), .02, .72)
    metal = _material("Original brushed steel", (.32, .35, .39), .88, .27)

    _cylinder("Handle steel shaft", shaft_radius, shaft_length, 0,
              48, .002, metal)
    _cylinder("Left six-sided head", head_radius, head_length, -center_distance,
              6, .004, rubber)
    _cylinder("Right six-sided head", head_radius, head_length, center_distance,
              6, .004, rubber)
    for sign, side in [(-1, "left"), (1, "right")]:
        _cylinder(f"{side.title()} steel collar", .028, .016, sign * .154,
                  48, .002, metal)

    parts = [o for o in bpy.context.scene.objects if o.get("ems_export")]
    if len(parts) != 5:
        raise RuntimeError("expected 5 procedural equipment meshes")

    _aim_camera((.62, -.87, .52))
    _studio_lighting(head_radius)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (.30, .30, .30)

    source_path = output / "asset.blend"
    glb_path = output / "asset.glb"
    png_path = output / "preview.png"
    bpy.ops.wm.save_as_mainfile(filepath=str(source_path))

    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path), export_format="GLB",
        use_selection=True, export_cameras=False, export_lights=False,
    )

    scene.render.filepath = str(png_path)
    bpy.ops.render.render(write_still=True)

    asset_id = f"{ASSET_FAMILY}.{mass_kg:g}kg"
    manifest = {
        "schema_version": "1.0",
        "asset_id": asset_id,
        "version": "0.1.0",
        "category": "free_weight",
        "subcategory": "hex_dumbbell",
        "variant": {"nominal_mass_kg": mass_kg,
                    "note": "Nominal family variant; actual mass not physically simulated"},
        "coordinate_system": "Blender Z-up, X axial; glTF export normalized to Y-up",
        "unit": "meter",
        "dimensions_m": {"length_x": round(outer_length, 6),
                         "width_y": round(2 * head_radius, 6),
                         "height_z": round(2 * head_radius, 6)},
        "grip_points": [
            {"id": "center_grip", "position_m": [0, 0, 0],
             "axis": [1, 0, 0], "radius_m": shaft_radius}
        ],
        "attachment_points": [
            {"id": "left_head", "position_m": [-center_distance, 0, 0]},
            {"id": "right_head", "position_m": [center_distance, 0, 0]}
        ],
        "contact_surfaces": [
            {"id": "left_head_outer",
             "point_m": [-outer_length / 2, 0, 0],
             "normal": [-1, 0, 0], "radius_m": head_radius},
            {"id": "right_head_outer",
             "point_m": [outer_length / 2, 0, 0],
             "normal": [1, 0, 0], "radius_m": head_radius},
        ],
        "collision_shapes": [
            {"id": "left_head", "shape": "cylinder", "center_m": [-center_distance, 0, 0],
             "axis": [1, 0, 0], "radius_m": head_radius, "length_m": head_length},
            {"id": "right_head", "shape": "cylinder", "center_m": [center_distance, 0, 0],
             "axis": [1, 0, 0], "radius_m": head_radius, "length_m": head_length},
            {"id": "shaft", "shape": "cylinder", "center_m": [0, 0, 0],
             "axis": [1, 0, 0], "radius_m": shaft_radius, "length_m": shaft_length},
        ],
        "kinematics": {"type": "rigid", "joints": []},
        "procedural_parameters": {"mass_kg": mass_kg, "head_radius_m": head_radius,
                                  "head_length_m": head_length,
                                  "shaft_length_m": shaft_length},
        "models": {"editable": "asset.blend", "distribution": "asset.glb",
                   "thumbnail": "preview.png"},
        "source": {"kind": "ORIGINAL_PROCEDURAL",
                   "script": "src/blender/generate_hex_dumbbell.py",
                   "script_sha256": _hash(SOURCE_FILE),
                   "blender_version": bpy.app.version_string},
        "licenses": {"geometry_owner": "Exercise Motion Studio project",
                     "origin": "Generated entirely from built-in Blender primitives",
                     "status": "PENDING",
                     "distribution_approved": False,
                     "reviewer": None},
        "qa": {"render_created": True, "glb_exported": True,
               "roundtrip": "NOT_TESTED", "human_visual_review": "PENDING",
               "commercial_approval": False},
        "file_sha256": {p.name: _hash(p) for p in (source_path, glb_path, png_path)},
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path = output / "asset.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    args_raw = []
    import sys
    if "--" in sys.argv:
        args_raw = sys.argv[sys.argv.index("--") + 1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--mass-kg", type=float, default=10.0)
    args = parser.parse_args(args_raw)
    result = generate(Path(args.output_dir).expanduser().resolve(), args.mass_kg)
    print(json.dumps({"generated_asset": result["asset_id"],
                      "commercial_approval": False}, ensure_ascii=False))
