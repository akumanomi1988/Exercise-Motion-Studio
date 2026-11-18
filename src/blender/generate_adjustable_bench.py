"""Original articulated adjustable gym bench. Authoring-only, not commercial-approved.

Usage:
blender -b --factory-startup --python-exit-code 10 --python \
  src/blender/generate_adjustable_bench.py -- --output-dir data/generated_assets/bench

The backrest is one rigid hinged part with a *real keyframed revolute joint*
(0, 30, 60 degrees). The mechanism has a pivot and hard mechanical limits in
metadata; it is not a physics simulation or human support/contact proof.
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

ASSET_ID = "ems.equipment.bench.adjustable.v1"
SOURCE = Path(__file__).resolve()
HINGE_NAME = "Backrest hinge"
BACKREST_NAME = "Backrest padded surface"
FRAME_NAME = "Fixed center spine"
KEYS_DEGREES = ((1, 0.0), (16, 30.0), (31, 60.0))
PIVOT = (0.08, 0.0, 0.49)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def material(name, color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        raise RuntimeError("Principled BSDF unavailable")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = (*color, 1)
    return mat


def part(name, at, size, mat, category, bevel=0.004):
    bpy.ops.mesh.primitive_cube_add(size=1, location=at)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Soft manufactured edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    obj["ems_export"] = True
    obj["part_type"] = category
    return obj


def cylinder(name, at, radius, depth, mat, category):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=radius, depth=depth, location=at,
        rotation=(math.pi / 2, 0, 0),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    obj["ems_export"] = True
    obj["part_type"] = category
    return obj


def studio():
    bpy.ops.object.camera_add(location=(1.65, -2.25, 1.60))
    cam = bpy.context.object
    cam.name = "Preview camera excluded from GLB"
    target = Vector((0.14, 0, 0.52))
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 1.95
    bpy.context.scene.camera = cam
    bpy.ops.mesh.primitive_plane_add(size=5, location=(0, 0, -0.016))
    floor = bpy.context.object
    floor.name = "Studio ground excluded from GLB"
    floor.data.materials.append(material(
        "Inspection charcoal floor", (.042, .055, .073), 0.0, .98))
    for name, at, energy in (
        ("Key", (-0.9, -1.0, 1.8), 260),
        ("Fill", (1.0, 0.7, 1.5), 140),
    ):
        bpy.ops.object.light_add(type="AREA", location=at)
        light = bpy.context.object
        light.name = f"Studio {name} excluded from GLB"
        light.data.energy = energy
        light.data.size = 2.0
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    if hasattr(scene.cycles, "use_denoising"):
        scene.cycles.use_denoising = False
    for layer in scene.view_layers:
        if hasattr(layer, "cycles") and hasattr(layer.cycles, "use_denoising"):
            layer.cycles.use_denoising = False
    scene.render.resolution_x = 720
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.10, 0.12, 0.14)


def generate(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    steel = material("Original graphite powder coat", (.075, .085, .10), .65, .35)
    metal = material("Original satin hinge steel", (.34, .38, .42), .85, .25)
    vinyl = material("Original textured black upholstery", (.035, .038, .048), .0, .82)
    accents = material("Original foot rubber", (.018, .020, .024), .0, .92)

    fixed = [
        part(FRAME_NAME, (.08, 0, .365), (1.0, .065, .055), steel, "fixed_frame"),
        part("Front vertical leg", (-.27, 0, .22), (.060, .068, .32), steel, "fixed_frame"),
        part("Rear vertical leg", (.52, 0, .22), (.060, .068, .32), steel, "fixed_frame"),
        part("Front ground crossbar", (-.27, 0, .07), (.075, .44, .065), steel, "fixed_frame"),
        part("Rear ground crossbar", (.52, 0, .07), (.075, .44, .065), steel, "fixed_frame"),
        part("Left front rubber foot", (-.27, -.185, .03), (.085, .067, .06), accents, "ground_contact"),
        part("Right front rubber foot", (-.27, .185, .03), (.085, .067, .06), accents, "ground_contact"),
        part("Left rear rubber foot", (.52, -.185, .03), (.085, .067, .06), accents, "ground_contact"),
        part("Right rear rubber foot", (.52, .185, .03), (.085, .067, .06), accents, "ground_contact"),
        part("Fixed seat padded surface", (-.177, 0, .49), (.44, .32, .085), vinyl, "seat"),
        cylinder("Backrest hinge pin", PIVOT, .028, .38, metal, "revolute_pivot"),
    ]

    hinge = bpy.data.objects.new(HINGE_NAME, None)
    bpy.context.collection.objects.link(hinge)
    hinge.empty_display_type = "ARROWS"
    hinge.empty_display_size = .10
    hinge.location = PIVOT
    hinge["ems_export"] = True
    hinge["joint_kind"] = "revolute"
    hinge["axis_local"] = [0.0, -1.0, 0.0]
    hinge["min_degrees"] = 0.0
    hinge["max_degrees"] = 60.0

    # Local coordinates relative to the pivot: the near edge is at x=0;
    # this moves rigidly as the empty rotates without scaling/penetrating.
    back = part(BACKREST_NAME, (.365, 0, 0), (.73, .32, .085), vinyl,
                "articulated_backrest", bevel=.013)
    back.parent = hinge
    back.location = (.365, 0, 0)
    bpy.context.view_layer.update()
    # One articulated telescoping link between the fixed chassis and a socket
    # on the underside of the backrest. Bake synchronized transforms every
    # frame so the support does not detach on glTF sampling between keyframes.
    # Its shaft length changes; structural load bearing is NOT simulated.
    support_anchor = Vector((.16, 0, .35))
    socket_local = Vector((.54, 0, -.06))
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=.016, depth=1.0, location=(0, 0, 0),
    )
    support = bpy.context.object
    support.name = "Telescoping backrest support"
    support.data.materials.append(metal)
    support["ems_export"] = True
    support["part_type"] = "telescopic_support"
    length_limits = []
    for frame in range(1, 32):
        degrees = (frame - 1) * 2.0
        theta = math.radians(degrees)
        hinge.rotation_euler = (0.0, -theta, 0.0)
        hinge.keyframe_insert(data_path="rotation_euler", frame=frame)
        # R_y(-theta) applied to a fixed backrest-local anchor.
        socket = Vector((
            PIVOT[0] + socket_local.x * math.cos(theta)
            - socket_local.z * math.sin(theta),
            0.0,
            PIVOT[2] + socket_local.x * math.sin(theta)
            + socket_local.z * math.cos(theta),
        ))
        axis = socket - support_anchor
        length_limits.append(axis.length)
        support.location = (socket + support_anchor) * .5
        support.rotation_euler = axis.to_track_quat("Z", "Y").to_euler()
        support.scale = (1.0, 1.0, axis.length)
        for prop in ("location", "rotation_euler", "scale"):
            support.keyframe_insert(data_path=prop, frame=frame)
    scene = bpy.context.scene
    scene.render.fps = 15
    scene.frame_start, scene.frame_end = 1, 31
    scene.frame_set(23)
    bpy.context.view_layer.update()

    studio()
    blend = out / "asset.blend"
    glb = out / "asset.glb"
    png = out / "preview.png"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in fixed + [hinge, back, support]:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = hinge
    bpy.ops.export_scene.gltf(
        filepath=str(glb), export_format="GLB", use_selection=True,
        export_animations=True, export_cameras=False, export_lights=False,
    )
    preview_files = {
        "preview_flat.png": 1,
        "preview.png": 23,
        "preview_upright.png": 31,
    }
    for preview_name, frame in preview_files.items():
        scene.frame_set(frame)
        scene.render.filepath = str(out / preview_name)
        bpy.ops.render.render(write_still=True)
    if not glb.is_file() or not png.is_file():
        raise RuntimeError("Blender did not export generated bench")

    manifest = {
        "schema_version": "1.0",
        "asset_id": ASSET_ID,
        "version": "0.1.0",
        "category": "bench",
        "subcategory": "adjustable",
        "variant": {"revolute_backrest_degrees": [0, 30, 60]},
        "coordinate_system": "Blender Z-up; glTF Y-up on export",
        "unit": "meter",
        "dimensions_m": {
            "length_x": 1.16, "width_y": .44, "height_z": 1.18,
        },
        "grip_points": [],
        "attachment_points": [
            {"id": "backrest_hinge", "position_m": list(PIVOT)},
            {"id": "front_ground_contact", "position_m": [-.27, 0, 0]},
            {"id": "rear_ground_contact", "position_m": [.52, 0, 0]},
        ],
        "contact_surfaces": [
            {"id": "seat", "part_id": "Fixed seat padded surface",
             "point_m": [-.177, 0, .5325], "normal": [0, 0, 1]},
            {"id": "back", "part_id": BACKREST_NAME,
             "reference_joint_degrees": 0,
             "point_m": [.445, 0, .5325], "normal": [0, 0, 1]},
        ],
        "collision_shapes": [
            {"id": "hinge", "shape": "cylinder", "center_m": list(PIVOT),
             "axis": [0, 1, 0], "radius_m": .028, "length_m": .38},
        ],
        "kinematics": {
            "type": "articulated",
            "timeline_fps": 15,
            "timeline_duration_seconds": 2.0,
            "baked_frames": 31,
            "parts": [FRAME_NAME, "Fixed seat padded surface", BACKREST_NAME],
            "joints": [
                {"id": "backrest_recline", "part": BACKREST_NAME,
                 "driver_node": HINGE_NAME,
                 "type": "revolute", "pivot_m": list(PIVOT),
                 "axis": [0, -1, 0], "min_degrees": 0,
                 "max_degrees": 60, "keyframes": [
                    {"frame": frame, "angle_degrees": degree}
                    for frame, degree in KEYS_DEGREES
                 ]},
            ],
            "linkages": [{
                "id": "telescoping_support",
                "part": "Telescoping backrest support",
                "type": "prismatic_length_driver",
                "fixed_anchor_m": list(support_anchor),
                "backrest_attachment_local_m": list(socket_local),
                "minimum_length_m": round(min(length_limits), 6),
                "maximum_length_m": round(max(length_limits), 6),
                "driven_by": "backrest_recline",
                "length_baked_per_frame": True,
                "load_rating": "NOT_VERIFIED",
            }],
            "contact_solver": "NOT_IMPLEMENTED",
            "seat_backrest_collision_qa": "NOT_IMPLEMENTED",
        },
        "models": {
            "editable": "asset.blend",
            "distribution": "asset.glb",
            "thumbnail": "preview.png",
            "technical_views": ["preview_flat.png", "preview_upright.png"],
        },
        "source": {
            "kind": "ORIGINAL_PROCEDURAL",
            "script": "src/blender/generate_adjustable_bench.py",
            "script_sha256": sha(SOURCE),
            "blender_version": bpy.app.version_string,
        },
        "licenses": {
            "geometry_owner": "Exercise Motion Studio project",
            "origin": "Own procedural geometry: native Blender primitives only",
            "status": "PENDING", "distribution_approved": False,
            "reviewer": None,
        },
        "qa": {
            "glb_exported": True, "render_created": True,
            "joint_animation": "NOT_TESTED",
            "telescoping_support_qa": "NOT_TESTED",
            "roundtrip": "NOT_TESTED",
            "dual_avatar_contact": "NOT_TESTED",
            "human_visual_review": "PENDING",
            "commercial_approval": False,
        },
        "file_sha256": {
            path.name: sha(path) for path in (
                blend, glb, png,
                out / "preview_flat.png", out / "preview_upright.png",
            )
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "asset.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    result = generate(Path(args.output_dir).resolve())
    print("EMS_BENCH_CREATED=" + json.dumps({
        "asset_id": result["asset_id"],
        "joint_count": len(result["kinematics"]["joints"]),
        "commercial_approval": False,
    }))
