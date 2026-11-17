"""Original, parameterized Olympic barbell with annular plates and collars.

Authoring only: Blender headless; outputs editable .blend, GLB, PNG and asset.json.
No exercise motion, avatar contact, physics-derived weight or commercial approval.
All geometry and preview materials are created from Blender primitives/meshes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

FAMILY = "ems.equipment.barbell.olympic"
SOURCE = Path(__file__).resolve()
SHAFT_HALF_M = 0.655
SLEEVE_LENGTH_M = 0.445
BAR_LENGTH_M = 2 * (SHAFT_HALF_M + SLEEVE_LENGTH_M)
SHAFT_RADIUS_M = 0.01425
SLEEVE_RADIUS_M = 0.025
PLATE_SPECS = {
    5: (0.160, 0.025),
    10: (0.190, 0.038),
    15: (0.205, 0.046),
    20: (0.225, 0.055),
    25: (0.230, 0.065),
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def material(name: str, rgb: tuple[float, float, float], metallic: float,
             roughness: float):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        raise RuntimeError("Principled BSDF missing")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = (*rgb, 1)
    return mat


def cylinder(name: str, x: float, depth: float, radius: float, mat):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64, radius=radius, depth=depth,
        rotation=(0, math.pi / 2, 0), location=(x, 0, 0),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    obj["ems_export"] = True
    obj["part_type"] = "shaft" if "shaft" in name else "sleeve"
    return obj


def annulus(name: str, x: float, depth: float,
            outer_radius: float, inner_radius: float, mat):
    """Watertight, true through-hole cylindrical plate; no Boolean operation."""
    if not (0 < inner_radius < outer_radius and depth > 0):
        raise ValueError("annular solid dimensions invalid")
    n = 64
    vertices = []
    for side in (-1, 1):
        for radius in (outer_radius, inner_radius):
            for i in range(n):
                theta = 2 * math.pi * i / n
                vertices.append((x + side * depth / 2,
                                 radius * math.cos(theta),
                                 radius * math.sin(theta)))

    def ix(side: int, layer: int, idx: int):
        return side * 2 * n + layer * n + (idx % n)

    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.extend((
            (ix(0, 0, i), ix(0, 0, j), ix(1, 0, j), ix(1, 0, i)),
            (ix(0, 1, j), ix(0, 1, i), ix(1, 1, i), ix(1, 1, j)),
            (ix(0, 0, j), ix(0, 0, i), ix(0, 1, i), ix(0, 1, j)),
            (ix(1, 0, i), ix(1, 0, j), ix(1, 1, j), ix(1, 1, i)),
        ))
    mesh = bpy.data.meshes.new(name + " procedural annulus")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj["ems_export"] = True
    obj["part_type"] = "plate" if "plate" in name else "collar"
    return obj


def studio(radius: float):
    bpy.ops.object.camera_add(location=(1.60, -2.55, 1.12))
    camera = bpy.context.object
    camera.name = "Inspection camera (not exported)"
    camera.rotation_euler = (Vector((0, 0, 0)) - camera.location).to_track_quat(
        "-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.95
    bpy.context.scene.camera = camera
    bpy.ops.mesh.primitive_plane_add(size=5, location=(0, 0, -radius - .008))
    floor = bpy.context.object
    floor.name = "Inspection ground (not exported)"
    floor.data.materials.append(material("Ground neutral", (.13, .15, .18), 0, .9))
    for name, pos, power in (
        ("Key", (-.8, -1.0, 1.6), 750),
        ("Fill", (1.0, .7, 1.3), 540),
    ):
        bpy.ops.object.light_add(type="AREA", location=pos)
        lamp = bpy.context.object
        lamp.name = f"Inspection {name} (not exported)"
        lamp.data.energy = power
        lamp.data.size = 2.0
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 12
    if hasattr(scene.cycles, "use_denoising"):
        scene.cycles.use_denoising = False
    for layer in scene.view_layers:
        if hasattr(layer, "cycles") and hasattr(layer.cycles, "use_denoising"):
            layer.cycles.use_denoising = False
    scene.render.resolution_x = 960
    scene.render.resolution_y = 480
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (.16, .17, .19)


def generate(output: Path, plate_mass_kg: int, plates_per_side: int):
    if type(plate_mass_kg) is not int or plate_mass_kg not in PLATE_SPECS:
        raise ValueError("plate-mass-kg must be one of 5, 10, 15, 20, 25")
    if type(plates_per_side) is not int or not (0 <= plates_per_side <= 4):
        raise ValueError("plates-per-side must be 0..4")
    radius, thickness = PLATE_SPECS[plate_mass_kg]
    if plates_per_side * thickness + 0.07 > SLEEVE_LENGTH_M:
        raise ValueError("plate stack exceeds usable sleeve length")
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    steel = material("Original polished steel", (.35, .40, .45), .88, .27)
    rubber = material("Original graphite bumper plates", (.045, .058, .070), .02, .76)
    rim = material("Original cobalt collar", (.035, .11, .22), .68, .32)

    cylinder("Bar axial shaft", 0, 2 * SHAFT_HALF_M, SHAFT_RADIUS_M, steel)
    plate_locations = []
    for sign, side in ((-1, "left"), (1, "right")):
        sleeve_center = sign * (SHAFT_HALF_M + SLEEVE_LENGTH_M / 2)
        cylinder(f"{side} loading sleeve", sleeve_center, SLEEVE_LENGTH_M,
                 SLEEVE_RADIUS_M, steel)
        annulus(f"{side} sleeve shoulder", sign * (SHAFT_HALF_M + .008),
                .016, .037, .025, steel)
        for index in range(plates_per_side):
            center = sign * (
                SHAFT_HALF_M + .022 + (index + .5) * thickness
            )
            annulus(f"{side} plate {index + 1}", center, thickness,
                    radius, .0255, rubber)
            plate_locations.append(center)
        collar_center = sign * (SHAFT_HALF_M + .040 +
                                plates_per_side * thickness)
        annulus(f"{side} lock collar", collar_center, .024, .039, .0254, rim)

    parts = sorted((o for o in bpy.context.scene.objects if o.get("ems_export")),
                   key=lambda item: item.name)
    expected_count = 7 + 2 * plates_per_side
    if len(parts) != expected_count:
        raise RuntimeError(f"wrong procedural mesh count {len(parts)} != {expected_count}")

    studio(radius)
    blend, glb, png = (output / name for name in
                       ("asset.blend", "asset.glb", "preview.png"))
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.export_scene.gltf(
        filepath=str(glb), export_format="GLB",
        use_selection=True, export_cameras=False, export_lights=False,
        export_animations=False,
    )
    bpy.context.scene.render.filepath = str(png)
    bpy.ops.render.render(write_still=True)
    if not all(p.is_file() and p.stat().st_size > 1024 for p in (blend, glb, png)):
        raise RuntimeError("Blender source/GLB/preview not generated")

    nominal_loaded = 20 + 2 * plate_mass_kg * plates_per_side
    asset = {
        "schema_version": "1.0", "asset_id":
            f"{FAMILY}.{plate_mass_kg}kgx{plates_per_side}",
        "version": "0.1.0", "category": "free_weight",
        "subcategory": "olympic_barbell_loaded",
        "variant": {
            "nominal_bar_mass_kg": 20,
            "nominal_plate_mass_kg": plate_mass_kg,
            "plates_per_side": plates_per_side,
            "nominal_total_mass_kg": nominal_loaded,
            "mass_is_physics_simulated": False,
        },
        "coordinate_system": "Blender Z-up X axial; GLB normalized to Y-up",
        "unit": "meter",
        "dimensions_m": {
            "length_x": BAR_LENGTH_M, "width_y": 2 * radius,
            "height_z": 2 * radius,
        },
        "grip_points": [
            {"id": "left_grip", "position_m": [-.42, 0, 0],
             "axis": [1, 0, 0], "radius_m": SHAFT_RADIUS_M},
            {"id": "right_grip", "position_m": [.42, 0, 0],
             "axis": [1, 0, 0], "radius_m": SHAFT_RADIUS_M},
        ],
        "grip_adjustment_range_m": {
            "left": [-.60, -.225], "right": [.225, .60],
        },
        "attachment_points": [
            {"id": "left_sleeve", "position_m": [-SHAFT_HALF_M, 0, 0]},
            {"id": "right_sleeve", "position_m": [SHAFT_HALF_M, 0, 0]},
        ],
        "contact_surfaces": [
            {"id": "left_outer", "point_m": [-BAR_LENGTH_M / 2, 0, 0],
             "normal": [-1, 0, 0]},
            {"id": "right_outer", "point_m": [BAR_LENGTH_M / 2, 0, 0],
             "normal": [1, 0, 0]},
        ],
        "collision_shapes": [
            {"id": "shaft", "shape": "cylinder", "center_m": [0, 0, 0],
             "axis": [1, 0, 0], "radius_m": SHAFT_RADIUS_M,
             "length_m": 2 * SHAFT_HALF_M},
        ] + [
            {"id": f"{side}_plate_{i+1}", "shape": "cylinder",
             "center_m": [sign * (SHAFT_HALF_M + .022 +
                          (i + .5) * thickness), 0, 0],
             "axis": [1, 0, 0], "radius_m": radius, "length_m": thickness}
            for sign, side in ((-1, "left"), (1, "right"))
            for i in range(plates_per_side)
        ],
        "kinematics": {
            "type": "rigid", "joints": [],
            "motion_source": "NOT_ANIMATED",
            "grip_ik_validation": "NOT_TESTED",
        },
        "part_mesh_count": expected_count,
        "plate_centers_m": sorted(plate_locations),
        "models": {
            "editable": "asset.blend", "distribution": "asset.glb",
            "thumbnail": "preview.png",
        },
        "source": {
            "kind": "ORIGINAL_PROCEDURAL",
            "script": "src/blender/generate_olympic_barbell.py",
            "script_sha256": sha(SOURCE),
            "blender_version": bpy.app.version_string,
        },
        "licenses": {
            "geometry_owner": "Exercise Motion Studio project",
            "origin": "Original Blender-generated geometry and materials",
            "status": "PENDING", "distribution_approved": False,
            "reviewer": None,
        },
        "qa": {
            "glb_exported": True, "roundtrip": "NOT_TESTED",
            "grip_contact": "NOT_TESTED", "human_visual_review": "PENDING",
            "commercial_approval": False,
        },
        "file_sha256": {p.name: sha(p) for p in (blend, glb, png)},
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "asset.json").write_text(
        json.dumps(asset, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("EMS_BAR_BUILD=" + json.dumps({
        "asset_id": asset["asset_id"], "parts": len(parts),
        "nominal_mass_kg": nominal_loaded, "commercial_approval": False,
    }))
    return asset


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--plate-mass-kg", type=int, default=20)
    parser.add_argument("--plates-per-side", type=int, default=1)
    options = parser.parse_args(argv)
    generate(options.output_dir.expanduser().resolve(), options.plate_mass_kg,
             options.plates_per_side)
