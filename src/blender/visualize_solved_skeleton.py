"""Diagnostic Blender visualization of fixed-length skeleton from a REAL video.

Input only: solved_skeleton.json produced by ems solve. Renders observed
direction + invariant-length 3D segments, WITHOUT inventing a skinned human.
No inverse kinematics, biomechanical validation, avatar or publishing approval.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def _mat(name, rgb):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = 0.55
    material.diffuse_color = (*rgb, 1)
    return material


def _aim(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _blender_position(skeleton_3d):
    if not isinstance(skeleton_3d, list) or len(skeleton_3d) != 3:
        raise ValueError("invalid solved skeleton point")
    if not all(isinstance(v, (int, float)) and math.isfinite(v)
               for v in skeleton_3d):
        raise ValueError("nonfinite solved skeleton point")
    # ems.solver: X = horizontal, Y = vertical, Z = approximate depth;
    # Blender: X horizontal, Z vertical, Y depth. No world calibration.
    return Vector((
        float(skeleton_3d[0]),
        float(skeleton_3d[2]),
        float(skeleton_3d[1]),
    ))


def generate(source: Path, output: Path, sample_fps: int):
    raw = json.loads(source.read_text(encoding="utf-8"))
    if (raw.get("data_type") != "INTERMEDIATE_SKELETON_NOT_FINAL_MOTION"
            or raw.get("method") != "MEDIAPIPE_HIP_RELATIVE_GEOMETRIC_CONSTRAINTS"
            or raw.get("qa", {}).get("commercial_approval") is not False):
        raise ValueError("only review-required real-capture solved skeleton accepted")
    if raw.get("qa", {}).get("max_solved_relative_segment_length_deviation", 1) > .01:
        raise ValueError("actual solved segment invariants failed")
    segments = raw.get("parent_child_segments", [])
    if not segments or len(segments) != 16:
        raise ValueError("skeleton contract requires 16 directed segments")
    joints = {raw.get("root_name", "pelvis")}
    for s in segments:
        joints.add(s["parent"])
        joints.add(s["child"])
    if len(joints) != 17:
        raise ValueError("expected 17 semantic joint names")
    frames = [f for f in raw.get("frames", [])
              if f.get("state") == "SOLVED_REVIEW_REQUIRED"]
    if len(frames) < 3:
        raise ValueError("not enough real solved observations")
    if not 2 <= sample_fps <= 30:
        raise ValueError("sample-fps out of range")
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    point_material = _mat("Constrained position: sea green", (.03, .8, .56))
    segment_material = _mat("Fixed measured limb: royal purple", (.38, .31, .92))
    points = {}
    for name in sorted(joints):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=8, ring_count=6, radius=.022
        )
        obj = bpy.context.object
        obj.name = "Constrained " + name
        obj.data.materials.append(point_material)
        obj.rotation_mode = "QUATERNION"
        points[name] = obj

    links = {}
    for item in segments:
        parent, child = item["parent"], item["child"]
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=.010, depth=1)
        obj = bpy.context.object
        obj.name = f"Fixed {parent}--{child}"
        obj.rotation_mode = "QUATERNION"
        obj.data.materials.append(segment_material)
        links[(parent, child)] = obj

    start = frames[0]["timestamp_ms"]
    last_frame = 0
    for observation in frames:
        frame_no = 1 + round((observation["timestamp_ms"] - start)
                             * sample_fps / 1000)
        if frame_no <= last_frame:
            raise ValueError("nonmonotonic capture timestamps")
        last_frame = frame_no
        xyz = {key: _blender_position(observation["joints"][key])
               for key in joints}
        for key, obj in points.items():
            obj.location = xyz[key]
            obj.keyframe_insert(data_path="location", frame=frame_no)
        for (parent, child), obj in links.items():
            axis = xyz[child] - xyz[parent]
            if axis.length <= .001:
                raise ValueError("invalid nearly zero constrained segment")
            obj.location = (xyz[parent] + xyz[child]) / 2
            obj.rotation_quaternion = axis.to_track_quat("Z", "Y")
            obj.scale = (1, 1, axis.length)
            for path in ("location", "rotation_quaternion", "scale"):
                obj.keyframe_insert(data_path=path, frame=frame_no)

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = last_frame
    scene.render.fps = sample_fps
    for obj in bpy.data.objects:
        if obj.animation_data and obj.animation_data.action:
            for curve in obj.animation_data.action.fcurves:
                for key in curve.keyframe_points:
                    key.interpolation = "LINEAR"

    renderable = [*points.values(), *links.values()]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in renderable:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = renderable[0]
    glb = output / "pose_debug.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(glb), export_format="GLB",
        use_selection=True, export_animations=True,
        export_cameras=False, export_lights=False,
    )
    if not glb.exists() or glb.stat().st_size < 4096:
        raise RuntimeError("did not produce an animated constrained GLB")
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.object.camera_add(location=(1.8, -3.3, 1.2))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.6
    _aim(camera, (0, 0, 0))
    scene.camera = camera
    bpy.ops.object.light_add(type="AREA", location=(1., -1.5, 3.))
    bpy.context.object.data.energy = 500
    bpy.context.object.data.size = 4
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 8
    if hasattr(scene.cycles, "use_denoising"):
        scene.cycles.use_denoising = False
    for layer in scene.view_layers:
        if hasattr(layer, "cycles") and hasattr(layer.cycles, "use_denoising"):
            layer.cycles.use_denoising = False
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (.018, .018, .022)

    frames_dir = output / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    count = min(8, max(2, last_frame - 1))
    sample = sorted({1 + round(i * (last_frame - 1) / (count - 1))
                     for i in range(count)})
    for idx, fno in enumerate(sample):
        scene.frame_set(fno)
        scene.render.filepath = str(frames_dir / f"frame_{idx:03d}.png")
        bpy.ops.render.render(write_still=True)
    shutil.copyfile(
        frames_dir / f"frame_{len(sample) // 2:03d}.png",
        output / "pose_debug.png",
    )
    result = {
        "status": "TECHNICAL_VISUALIZATION_ONLY",
        "representation": "FIXED_LENGTH_INTERMEDIATE_SKELETON",
        "sampled_from": "REAL_HUMAN_VIDEO_POSE",
        "source_sha256": raw["source_sha256"],
        "model_sha256": raw["model_sha256"],
        "animation_frames": last_frame,
        "render_samples": sample,
        "animated_objects": len(renderable),
        "nominal_segments": len(segments),
        "max_solved_relative_segment_length_deviation":
            raw["qa"]["max_solved_relative_segment_length_deviation"],
        "glb_file": "pose_debug.glb",
        "preview_file": "pose_debug.png",
        "animation_webp": "NOT_GENERATED_BY_BLENDER",
        "avatar_model": "NONE",
        "retarget": "NOT_DONE",
        "biomechanics_qa": "NOT_DONE",
        "human_visual_approval": "NOT_DONE",
        "commercial_approval": False,
    }
    (output / "debug_manifest.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("EMS_REAL_SOLVED_DEBUG=" + json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser.add_argument("--solved", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sample-fps", type=int, default=6)
    args = parser.parse_args(argv)
    generate(args.solved.resolve(strict=True), args.output_dir.resolve(),
             args.sample_fps)
