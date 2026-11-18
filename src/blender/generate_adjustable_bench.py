"""Original articulated adjustable gym bench (technical asset, NOT approved).

Generated geometry, editable Blender source, skinned-independent GLB animation,
three-dimensional seat/backrest contact and telescoping supports. No external
models, commercial rights sign-off, load rating or human exercise QA claimed.
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
from mathutils import Quaternion, Vector

FAMILY = "ems.equipment.bench.adjustable"
SOURCE = Path(__file__).resolve()
HINGE = Vector((0.0, -0.18, 0.50))
BACK_LENGTH = 0.92
BASE_Y = 0.08
BASE_Z = 0.20
TIP_DISTANCE = 0.63
FRAMES = 49
FPS = 24


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require(value, reason):
    if not value:
        raise ValueError(reason)


def material(name, rgb, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    require(bsdf is not None, "Principled shader unavailable")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = (*rgb, 1.0)
    return mat


def box(name, dims, center, mat, *, part="static", bevel=0.006):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.location = center
    o.data.materials.append(mat)
    if bevel:
        mod = o.modifiers.new("Rounded manufactured edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    o["ems_export"] = True
    o["part_type"] = part
    return o


def rod(name, radius, mat, *, part):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=1.0)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    o.rotation_mode = "QUATERNION"
    o["ems_export"] = True
    o["part_type"] = part
    return o


def position_rod(obj, origin, target, start_distance, end_distance, frame):
    axis = target - origin
    length = axis.length
    require(length + 1e-6 >= end_distance > start_distance >= 0.0,
            "telescoping brace cannot reach backrest pivot")
    unit = axis.normalized()
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(unit)
    obj.location = origin + unit * ((start_distance + end_distance) / 2)
    obj.scale = (1.0, 1.0, end_distance - start_distance)
    for path in ("location", "rotation_quaternion", "scale"):
        obj.keyframe_insert(data_path=path, frame=frame)


def make_support(side, metal, rod_metal):
    x = side * 0.112
    outer = rod(f"Telescoping casing {'L' if side < 0 else 'R'}",
                .019, metal, part="telescoping_casing")
    inner = rod(f"Telescoping rod {'L' if side < 0 else 'R'}",
                .011, rod_metal, part="telescoping_rod")
    return x, outer, inner


def apply_support(support, angle, frame):
    x, casing, inner = support
    radians = math.radians(angle)
    origin = Vector((x, BASE_Y, BASE_Z))
    target = Vector((x,
                     HINGE.y + TIP_DISTANCE * math.cos(radians),
                     HINGE.z + TIP_DISTANCE * math.sin(radians)))
    distance = (target - origin).length
    # The rod overlaps the 0.29 m fixed casing by 0.10 m; exposed length
    # increases as the backrest rises. This is geometric kinematics, not
    # a force simulation or safe load-bearing mechanical specification.
    require(distance > 0.35, "brace collapses below operating length")
    position_rod(casing, origin, target, 0.0, 0.29, frame)
    position_rod(inner, origin, target, 0.19, distance, frame)


def studio():
    scene = bpy.context.scene
    bpy.ops.object.camera_add(location=(1.65, -2.1, 1.40))
    cam = bpy.context.object
    cam.name = "QA camera (not exported)"
    cam.rotation_euler = (Vector((0, 0.04, .55)) - cam.location).to_track_quat(
        "-Z", "Y").to_euler()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 2.4
    scene.camera = cam
    for name, pos, power in (("Key", (1.2, -.8, 2), 500),
                             ("Fill", (-.7, 1.2, 1.6), 300)):
        bpy.ops.object.light_add(type="AREA", location=pos)
        lamp = bpy.context.object
        lamp.name = name + " preview light (not exported)"
        lamp.data.energy = power
        lamp.data.size = 1.6
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 8
    scene.render.resolution_x = 768
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (.13, .14, .16)


def world_bounds(objects, scene, frames):
    mn = Vector((float("inf"),) * 3)
    mx = Vector((-float("inf"),) * 3)
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for obj in objects:
            for corner in obj.bound_box:
                v = obj.matrix_world @ Vector(corner)
                for axis in range(3):
                    mn[axis] = min(mn[axis], v[axis])
                    mx[axis] = max(mx[axis], v[axis])
    return [round(float(mx[i] - mn[i]), 6) for i in range(3)]


def generate(output: Path, back_angle_deg: int):
    require(type(back_angle_deg) is int and back_angle_deg in (0, 30, 45, 60, 75),
            "back-angle-deg must be one of 0,30,45,60,75")
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    steel = material("Original graphite steel", (.095, .12, .15), .72, .33)
    bright = material("Original silver adjusting rods", (.45, .48, .52), .84, .28)
    vinyl = material("Original graphite padding", (.028, .037, .050), .01, .76)
    rubber = material("Original rubber feet", (.035, .04, .048), .0, .88)

    for x in (-.155, .155):
        box(f"Base rail {x}", (.055, 1.28, .064), (x, .0, .20), steel)
        for y in (-.42, .36):
            box(f"Vertical support {x} {y}", (.057, .07, .36),
                (x, y, .35), steel)
    for y in (-.53, .53):
        box(f"Wide foot {y}", (.68, .095, .06), (0, y, .065), steel)
        for x in (-.31, .31):
            box(f"Grip rubber {x} {y}", (.075, .105, .025),
                (x, y, .023), rubber)
    box("Fixed seat pad", (.36, .40, .08), (0, -.385, .50),
        vinyl, part="seat_contact", bevel=.025)
    back = box("Moving backrest pad", (.34, BACK_LENGTH, .08), (0, 0, 0),
               vinyl, part="backrest_contact", bevel=.025)
    # Move mesh vertices, not object origin: origin is exactly the real hinge.
    for vertex in back.data.vertices:
        vertex.co.y += BACK_LENGTH / 2
    back.location = HINGE
    back.rotation_mode = "QUATERNION"
    pivot = rod("Backrest hinge axle", .022, bright, part="revolute_pivot")
    pivot.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(
        Vector((1, 0, 0)))
    pivot.location = HINGE
    pivot.scale = (1, 1, .42)

    supports = [make_support(sign, steel, bright) for sign in (-1, 1)]
    delta = 15 if back_angle_deg <= 60 else -15
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = FRAMES
    for fno in range(1, FRAMES + 1):
        angle = back_angle_deg + delta * (
            1 - math.cos(2 * math.pi * (fno - 1) / (FRAMES - 1))
        ) / 2
        back.rotation_quaternion = Quaternion((1, 0, 0), math.radians(angle))
        back.keyframe_insert(data_path="rotation_quaternion", frame=fno)
        for support in supports:
            apply_support(support, angle, fno)
    for action in bpy.data.actions:
        if hasattr(action, "fcurves"):
            for curve in action.fcurves:
                for key in curve.keyframe_points:
                    key.interpolation = "LINEAR"

    parts = sorted((obj for obj in scene.objects if obj.get("ems_export")),
                   key=lambda obj: obj.name)
    require(len(parts) == 19, "procedural bench lacks frame/padding/support")
    dims = world_bounds(parts, scene, (1, 25, 49))
    scene.frame_set(1)
    studio()
    source, glb, preview = (
        output / "asset.blend", output / "asset.glb", output / "preview.png"
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = back
    bpy.ops.export_scene.gltf(
        filepath=str(glb), export_format="GLB", use_selection=True,
        export_animations=True, export_cameras=False, export_lights=False,
    )
    scene.render.filepath = str(preview)
    bpy.ops.render.render(write_still=True)
    require(all(p.is_file() and p.stat().st_size > 1024
                for p in (source, glb, preview)), "Blender asset export incomplete")
    a = math.radians(back_angle_deg)
    manifest = {
        "schema_version": "1.0",
        "asset_id": f"{FAMILY}.{back_angle_deg}deg",
        "version": "0.1.0",
        "category": "bench",
        "subcategory": "adjustable",
        "variant": {"back_angle_degrees": back_angle_deg,
                    "animation_type": "TECHNICAL_ADJUSTMENT_NOT_EXERCISE"},
        "unit": "meter",
        "coordinate_system": "Blender Z-up; glTF Y-up",
        "dimensions_m": dict(zip(("length_x", "width_y", "height_z"), dims)),
        "grip_points": [],
        "attachment_points": [
            {"id": "backrest_hinge", "position_m": list(HINGE)},
            {"id": "left_brace_base", "position_m": [-.112, BASE_Y, BASE_Z]},
            {"id": "right_brace_base", "position_m": [.112, BASE_Y, BASE_Z]},
        ],
        "contact_surfaces": [
            {"id": "seat_top", "point_m": [0, -.385, .54],
             "normal": [0, 0, 1]},
            {"id": "backrest_top",
             "point_m": [0, HINGE.y + .46 * math.cos(a) - .04 * math.sin(a),
                         HINGE.z + .46 * math.sin(a) + .04 * math.cos(a)],
             "normal": [0, -math.sin(a), math.cos(a)]},
        ],
        "collision_shapes": [
            {"id": "seat", "shape": "box",
             "center_m": [0, -.385, .5], "size_m": [.36, .4, .08],
             "rotation_xyzw": [0, 0, 0, 1]},
            {"id": "backrest", "shape": "box",
             "center_m": [0, HINGE.y + .46 * math.cos(a),
                         HINGE.z + .46 * math.sin(a)],
             "size_m": [.34, BACK_LENGTH, .08],
             "rotation_xyzw": [math.sin(a/2), 0, 0, math.cos(a/2)]},
        ],
        "kinematics": {
            "type": "articulated",
            "joints": [
                {"id": "backrest_hinge", "type": "revolute",
                 "part": "Moving backrest pad", "axis": [1, 0, 0],
                 "pivot_m": list(HINGE), "min_degrees": 0, "max_degrees": 75,
                 "initial_degrees": back_angle_deg},
            ],
            "transmissions": [
                {"type": "telescoping", "parts": [
                    "Telescoping casing L", "Telescoping rod L",
                    "Telescoping casing R", "Telescoping rod R"],
                 "motion": "analytic_two_endpoint_kinematics"},
            ],
            "preview_animation": {"frames": FRAMES, "fps": FPS,
                                  "peak_angle_degrees": back_angle_deg + delta},
            "load_rating": "NOT_CERTIFIED", "contact_ik": "NOT_TESTED",
        },
        "models": {"editable": "asset.blend", "distribution": "asset.glb",
                   "thumbnail": "preview.png"},
        "source": {"kind": "ORIGINAL_PROCEDURAL",
                   "script": "src/blender/generate_adjustable_bench.py",
                   "script_sha256": sha(SOURCE),
                   "blender_version": bpy.app.version_string},
        "licenses": {"geometry_owner": "Exercise Motion Studio project",
                     "origin": "Original Blender primitives only",
                     "status": "PENDING", "distribution_approved": False,
                     "reviewer": None},
        "qa": {"roundtrip": "NOT_TESTED", "human_visual_review": "PENDING",
               "dual_avatar_contact": "NOT_TESTED", "commercial_approval": False},
        "file_sha256": {p.name: sha(p) for p in (source, glb, preview)},
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "asset.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--back-angle-deg", type=int, default=45)
    a = parser.parse_args(argv)
    r = generate(a.output_dir.resolve(), a.back_angle_deg)
    print("EMS_ADJUSTABLE_BENCH=" + json.dumps({
        "asset_id": r["asset_id"], "rights": "PENDING",
        "kinematics": r["kinematics"]["type"],
    }))
