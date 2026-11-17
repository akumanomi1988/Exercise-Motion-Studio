"""Render ACTUAL captured landmark motion as a diagnostic animated GLB.

This is NOT retargeting, not a humanoid avatar and not commercial output.
The figures visualize 33 hip-relative, uncalibrated world landmarks exactly as
produced by MediaPipe, using spheres + links keyed at captured timestamps.
Do not treat this as a human mesh, gait analysis or G1 accepted result.

Usage:
  blender -b --python src/blender/visualize_raw_pose.py -- \
    --pose-raw data/qa-inference/pose_raw.json \
    --output-dir data/qa-inference/diagnostic
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

# Selected visible bone-like links are only diagnostic, not a rig hierarchy.
LINKS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24), (23, 25), (25, 27),
    (24, 26), (26, 28), (27, 29), (29, 31),
    (28, 30), (30, 32), (11, 0), (12, 0),
]


def _safe_observations(path: Path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    if (raw.get("data_type") != "MEDIAPIPE_RAW_POSE_OBSERVATIONS"
            or raw.get("method") != "video_inference_real"):
        raise ValueError("only genuine inference output is accepted")
    if raw.get("space", {}).get("absolute_root_motion") is not False:
        raise ValueError("unexpected coordinate space")
    frames = [f for f in raw.get("frames", []) if f.get("state") == "DETECTED"]
    if len(frames) < 2:
        raise ValueError("not enough genuine detected human frames")
    if not all(len(f.get("world_landmarks", [])) == 33 for f in frames):
        raise ValueError("each frame must contain 33 world landmarks")
    for f in frames:
        for p in f["world_landmarks"]:
            if not all(math.isfinite(float(p[key])) for key in ("x", "y", "z")):
                raise ValueError("nonfinite input landmarks")
    return raw, frames


def _mat(name, color):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = .5
    return result


def _loc(p):
    # Diagnostic axes: MediaPipe +Y (image-down) mapped to Blender -Z;
    # relative hip center remains at origin. NOT an anatomical calibration.
    return Vector((float(p["x"]), -float(p["z"]), -float(p["y"])))


def _aim(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def generate(pose_raw: Path, out: Path):
    raw, frames = _safe_observations(pose_raw)
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    joint_mat = _mat("Observed landmark: cyan", (.06, .67, .85))
    link_mat = _mat("Uncalibrated joint link: amber", (.95, .42, .08))
    joints = []
    for index in range(33):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=.022)
        obj = bpy.context.object
        obj.name = f"Observed J{index:02d}"
        obj.data.materials.append(joint_mat)
        obj["diagnostic_only"] = True
        obj.rotation_mode = "QUATERNION"
        joints.append(obj)
    segments = []
    for a, b in LINKS:
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=.009, depth=1)
        obj = bpy.context.object
        obj.name = f"Observed link {a:02d}-{b:02d}"
        obj.data.materials.append(link_mat)
        obj.rotation_mode = "QUATERNION"
        obj["diagnostic_only"] = True
        segments.append((a, b, obj))

    original_start_ms = frames[0]["timestamp_ms"]
    sample_fps = int(raw["video"]["sampling_fps"])
    bpy.context.scene.render.fps = sample_fps
    scene = bpy.context.scene
    previous = 0
    for observation in frames:
        fno = 1 + round((observation["timestamp_ms"] - original_start_ms)
                        * sample_fps / 1000)
        if fno <= previous:
            raise ValueError("nonmonotonic resampled frame timestamps")
        previous = fno
        xyz = [_loc(p) for p in observation["world_landmarks"]]
        for i, obj in enumerate(joints):
            obj.location = xyz[i]
            obj.keyframe_insert(data_path="location", frame=fno)
        for a, b, obj in segments:
            diff = xyz[b] - xyz[a]
            distance = max(diff.length, .0001)
            obj.location = (xyz[a] + xyz[b]) / 2
            obj.rotation_quaternion = diff.to_track_quat("Z", "Y")
            obj.scale = (1, 1, distance)
            for prop in ("location", "rotation_quaternion", "scale"):
                obj.keyframe_insert(data_path=prop, frame=fno)
    scene.frame_start = 1
    scene.frame_end = previous
    for obj in bpy.data.objects:
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                for key in fc.keyframe_points:
                    key.interpolation = "LINEAR"

    objects = joints + [x[2] for x in segments]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    glb = out / "pose_debug.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(glb), export_format="GLB",
        use_selection=True, export_animations=True,
        export_cameras=False, export_lights=False,
    )
    if not glb.exists() or glb.stat().st_size < 4096:
        raise RuntimeError("animated diagnostic GLB export failed")

    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.object.camera_add(location=(1.8, -3.3, 1.2))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.6
    _aim(camera, (0, 0, 0))
    scene.camera = camera
    bpy.ops.object.light_add(type="AREA", location=(1.0, -1.5, 3.0))
    bpy.context.object.data.energy = 500
    bpy.context.object.data.size = 4
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 8
    # Ubuntu-packaged Blender may not ship OpenImageDenoiser; this renderer
    # does not need denoising for diagnostic colored landmarks.
    if hasattr(scene.cycles, "use_denoising"):
        scene.cycles.use_denoising = False
    for layer in scene.view_layers:
        if hasattr(layer, "cycles") and hasattr(layer.cycles, "use_denoising"):
            layer.cycles.use_denoising = False
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (.018, .018, .022)

    frames_dir = out / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    sample_count = min(8, max(2, scene.frame_end - 1))
    render_frames = sorted({
        1 + round(i * (scene.frame_end - 1) / (sample_count - 1))
        for i in range(sample_count)
    })
    for i, fno in enumerate(render_frames):
        scene.frame_set(fno)
        scene.render.filepath = str(frames_dir / f"frame_{i:03d}.png")
        bpy.ops.render.render(write_still=True)
    # A stand-alone PNG at the middle of the actual captured motion.
    import shutil
    shutil.copyfile(frames_dir / f"frame_{len(render_frames) // 2:03d}.png",
                    out / "pose_debug.png")
    report = {
        "status": "TECHNICAL_VISUALIZATION_ONLY",
        "raw_pose_sha256": raw["source_sha256"],
        "source_type": "HUMAN_VIDEO_INFERENCE",
        "animation_frames": scene.frame_end,
        "render_samples": render_frames,
        "animated_objects": len(objects),
        "glb_file": "pose_debug.glb",
        "preview_file": "pose_debug.png",
        "animation_webp": "NOT_GENERATED_BY_BLENDER",
        "retarget": "NOT_DONE",
        "avatar_model": "NONE",
        "biomechanics_qa": "NOT_DONE",
        "absolute_world_alignment": "UNCALIBRATED",
        "rights_review": "REVIEW_REQUIRED",
        "human_visual_approval": "NOT_DONE",
        "commercial_approval": False,
    }
    (out / "debug_manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("EMS_REAL_VIDEO_DEBUG=" + json.dumps(report))
    return report


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    a.add_argument("--pose-raw", required=True, type=Path)
    a.add_argument("--output-dir", required=True, type=Path)
    args = a.parse_args(argv)
    generate(args.pose_raw.resolve(strict=True), args.output_dir.resolve())
