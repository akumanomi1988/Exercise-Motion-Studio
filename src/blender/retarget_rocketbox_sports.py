"""Retarget an authentic solved MediaPipe recording onto a real Microsoft Rocketbox skinned rig.

This is an *experimental observed-direction* transfer to a deformable Microsoft Rocketbox
body, never a validated motion.json / foot IK / joint-twist / commercial clip.
The solver's relative coordinates cannot recover absolute root translation.
No procedural substitute movements are generated or silently approved.

Requires a previously generated Rocketbox MIT sports avatar .glb and a SHA-identified
solved_skeleton.json from the authorized real-video capture workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

BONE_TARGETS = (
    ("Bip01 Spine", "pelvis", "chest"),
    ("Bip01 Spine1", "pelvis", "chest"),
    ("Bip01 Spine2", "pelvis", "chest"),
    ("Bip01 L Clavicle", "chest", "leftShoulder"),
    ("Bip01 R Clavicle", "chest", "rightShoulder"),
    ("Bip01 L UpperArm", "leftShoulder", "leftElbow"),
    ("Bip01 R UpperArm", "rightShoulder", "rightElbow"),
    ("Bip01 L Forearm", "leftElbow", "leftWrist"),
    ("Bip01 R Forearm", "rightElbow", "rightWrist"),
    ("Bip01 L Thigh", "leftHip", "leftKnee"),
    ("Bip01 R Thigh", "rightHip", "rightKnee"),
    ("Bip01 L Calf", "leftKnee", "leftAnkle"),
    ("Bip01 R Calf", "rightKnee", "rightAnkle"),
    ("Bip01 L Foot", "leftAnkle", "leftToe"),
    ("Bip01 R Foot", "rightAnkle", "rightToe"),
    ("Bip01 Neck", "pelvis", "chest"),
)
_SPINE_BLEND = {"Bip01 Spine": 1./3., "Bip01 Spine1": 1./2.,
                "Bip01 Spine2": 1.0}
SHA256 = re.compile(r"^[a-f0-9]{64}$")


def require(ok: bool, message: str):
    if not ok:
        raise ValueError(message)


def hashfile(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fd:
        for block in iter(lambda: fd.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def from_solved(vector: list[float]) -> Vector:
    """Proper rotation Y-up solved frame to Blender Z-up (determinant +1).

    X = horizontal; Blender Y = negative solver depth, Z = solver up.
    The solver frame is uncalibrated and not a world-space reconstruction.
    """
    require(isinstance(vector, list) and len(vector) == 3,
            "missing three-dimensional solved joint")
    require(all(type(v) in (int, float) and math.isfinite(v) for v in vector),
            "invalid/nonfinite solved joint")
    return Vector((float(vector[0]), -float(vector[2]), float(vector[1])))


def direction(a: Vector, b: Vector) -> Vector:
    v = b - a
    require(v.length > 1e-5, "degenerate observed or rest body direction")
    return v.normalized()


def basis(lateral: Vector, up: Vector) -> Matrix:
    x = lateral.normalized()
    z0 = up - up.dot(x) * x
    require(z0.length > .04, "unable to orient observed body; ambiguous torso")
    z = z0.normalized()
    y = z.cross(x).normalized()
    result = Matrix(((x.x, y.x, z.x),
                     (x.y, y.y, z.y),
                     (x.z, y.z, z.z)))
    require(result.determinant() > .99, "unexpected reflected basis")
    return result


def infer_alignment(frames: list[dict], rig) -> Matrix:
    """Fix one rotation from measured body left/up to rig left/up.

    One-camera depth ambiguity survives this calibration. Rotating each frame
    to face forward would discard authentic turning motion, so do not do it.
    """
    lateral = Vector((0, 0, 0))
    up = Vector((0, 0, 0))
    for observation in frames[:min(len(frames), 5)]:
        p = {name: from_solved(v) for name, v in observation["joints"].items()}
        lateral += (p["leftShoulder"] - p["rightShoulder"])
        lateral += (p["leftHip"] - p["rightHip"])
        up += p["chest"] - p["pelvis"]
    source_basis = basis(lateral, up)
    bones = rig.data.bones
    rest_lateral = bones["Bip01 L UpperArm"].head_local - bones["Bip01 R UpperArm"].head_local
    rest_up = bones["Bip01 Spine2"].tail_local - bones["Bip01 Pelvis"].head_local
    rig_basis = basis(rest_lateral, rest_up)
    transform = rig_basis @ source_basis.transposed()
    require(abs(transform.determinant() - 1) < 1e-3,
            "failed orientation calibration")
    return transform


def choose_reference(frames: list[dict]) -> dict:
    """Select a measured relatively upright pose as zero-swing calibration.

    This is a visual stabilization heuristic, NOT an assertion that a
    biomechanically correct standing frame was observed or approved.
    """
    def upright_score(sample):
        j = sample["joints"]
        p = {k: from_solved(v) for k, v in j.items()}
        torso = direction(p["pelvis"], p["chest"])
        supporting_leg = max(
            -(direction(p["leftHip"], p["leftAnkle"]).z),
            -(direction(p["rightHip"], p["rightAnkle"]).z),
        )
        return .70 * torso.z + .30 * supporting_leg

    return max(frames, key=upright_score)


def _find_real_skin():
    rigs = [x for x in bpy.context.scene.objects if x.type == "ARMATURE"]
    require(len(rigs) == 1, "expected exactly one imported skinned rig")
    rig = rigs[0]
    meshes = [obj for obj in bpy.context.scene.objects
              if obj.type == "MESH" and obj.data and
              len(obj.data.vertices) > 1000 and
              any(m.type == "ARMATURE" and m.object == rig
                  for m in obj.modifiers)]
    require(len(meshes) >= 1, "no authentic skinned geometry bound to the rig")
    require(len(rig.data.bones) == 80, "wrong pinned Rocketbox sport skeleton bone count")
    require(all(name in rig.pose.bones for name, _, _ in BONE_TARGETS),
            "Rocketbox skeleton missing a mapped semantic bone")
    mesh = max(meshes, key=lambda item: len(item.data.vertices))
    require(sum(bool(v.groups) for v in mesh.data.vertices) > 1000,
            "mesh has no actual skin weights")
    return rig, mesh


def _set_global_direction(posebone, desired: Vector):
    """Aim a bone using ONLY a local quaternion; never write posebone.matrix.

    Setting posebone.matrix as an armature-global absolute transform can set
    implicit local bone translations to counter parent movement. The previous
    retarget only keyframed rotation and silently left those translations
    inconsistent across frames/GLB. Solve the minimal swing in the bone's
    animated LOCAL rotation basis with the actual parent pose evaluated.
    This cannot infer axial twist, depth or medically valid constraints.
    """
    require(posebone.rotation_mode == "QUATERNION",
            "local swing requires quaternion rotation mode")
    require(posebone.location.length < 1e-6,
            "a deform bone acquired a translation before retarget")
    bpy.context.view_layer.update()
    before_orientation = posebone.matrix.to_quaternion()
    current = direction(posebone.head, posebone.tail)
    swing_armature = current.rotation_difference(desired)
    # R_after = R_before * R_local, and the required world-space
    # orientation is swing_armature * R_before. Conjugate into the bone's
    # current LOCAL pose basis, without touching its translation/scale.
    swing_local = (before_orientation.inverted()
                   @ swing_armature @ before_orientation)
    posebone.rotation_quaternion = (
        swing_local @ posebone.rotation_quaternion
    ).normalized()
    bpy.context.view_layer.update()
    actual = direction(posebone.head, posebone.tail)
    angular_error = math.degrees(actual.angle(desired))
    require(math.isfinite(angular_error) and angular_error < .5,
            f"bone {posebone.name} failed local swing aim: "
            f"{angular_error:.3f} degrees")
    require(posebone.location.length < 1e-6,
            f"unexpected translated deform bone: {posebone.name}")
    # Local swing is the shortest correction: rotation_about_axial is not
    # estimated; do not report invented twist fidelity.
    return angular_error, 0.0


def _studio(mesh, rig):
    bpy.context.view_layer.update()
    bounds = [mesh.matrix_world @ Vector(c) for c in mesh.bound_box]
    low = Vector([min(v[i] for v in bounds) for i in range(3)])
    high = Vector([max(v[i] for v in bounds) for i in range(3)])
    center = (low + high) * .5
    height = high.z - low.z
    require(1.2 < height < 2.5, "imported human dimensions not plausible")
    bpy.ops.object.camera_add(location=center + Vector(
        (height * .70, -height * 2.55, height * .20)
    ))
    camera = bpy.context.object
    camera.name = "Review camera excluded from GLB"
    camera.rotation_euler = (center - camera.location).to_track_quat(
        "-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = height * 1.50
    scene = bpy.context.scene
    scene.camera = camera
    for name, pos, energy in (
        ("Key", center + Vector((1.2, -1.5, 2.3)), 650),
        ("Fill", center + Vector((-1.5, .8, 1.2)), 330),
    ):
        bpy.ops.object.light_add(type="AREA", location=pos)
        lamp = bpy.context.object
        lamp.name = "Review " + name + " light excluded from GLB"
        lamp.data.energy = energy
        lamp.data.size = 2.5
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
    scene.render.film_transparent = False
    scene.world.color = (.085, .09, .10)


def _sample_skin_vertices(mesh):
    """Sample evaluated *mesh* vertices, not armature transforms alone."""
    dep = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh.evaluated_get(dep)
    geometry = evaluated.to_mesh()
    try:
        step = max(1, len(geometry.vertices) // 300)
        return [tuple(geometry.vertices[i].co)
                for i in range(0, len(geometry.vertices), step)]
    finally:
        evaluated.to_mesh_clear()


def generate(source: Path, avatar: Path, output: Path,
             attribution: Path, fps: int):
    require(2 <= fps <= 30, "fps out of supported range")
    raw = json.loads(source.read_text(encoding="utf-8"))
    require(raw.get("data_type") == "INTERMEDIATE_SKELETON_NOT_FINAL_MOTION",
            "retarget requires intermediate from actual capture")
    require(raw.get("method") == "MEDIAPIPE_HIP_RELATIVE_GEOMETRIC_CONSTRAINTS",
            "unsupported or procedural pose data")
    require(raw.get("coordinate_system") ==
            "APPROX_RH_Y_UP_RELATIVE_UNCALIBRATED",
            "unexpected solver coordinate system")
    require(raw.get("qa", {}).get("status") == "REVIEW_REQUIRED" and
            raw["qa"].get("commercial_approval") is False,
            "source solver review cannot be overridden")
    require(raw["qa"].get("max_solved_relative_segment_length_deviation", 1) <= .01,
            "unreliable segment length invariants")
    for k in ("source_sha256", "model_sha256"):
        require(isinstance(raw.get(k), str) and SHA256.fullmatch(raw[k]),
                "missing real source/model SHA: " + k)
    require(attribution.is_file() and "CC BY-SA 4.0" in
            attribution.read_text(encoding="utf-8"),
            "actual reference attribution / sharealike obligations missing")

    frames_all = raw.get("frames")
    require(isinstance(frames_all, list) and len(frames_all) >= 3,
            "too few captured frames")
    stamps = [v.get("timestamp_ms") for v in frames_all]
    require(all(type(t) is int for t in stamps) and
            all(a < b for a, b in zip(stamps, stamps[1:])),
            "raw capture timestamps invalid")
    captured = [v for v in frames_all
                if v.get("state") == "SOLVED_REVIEW_REQUIRED"]
    require(len(captured) >= 3, "no credible sequence of real solved poses")
    required_joints = {x for _, p, c in BONE_TARGETS for x in (p, c)}
    for obs in captured:
        joints = obs.get("joints", {})
        require(required_joints.issubset(joints), "incomplete observed joints")
        for name in required_joints:
            from_solved(joints[name])

    meta_path = avatar / "asset.json"
    require(meta_path.is_file(), "avatar provenance manifest missing")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    require(meta.get("rig", {}).get("profile_id") == "ems.humanoid.rocketbox.sports.v1",
            "retarget requires pinned Rocketbox shared skeletal profile")
    require(meta.get("source", {}).get("upstream_commit") ==
            "0943055db6ec570bcef9f2c8b41c9e5467c808f9",
            "unexpected avatar provenance")
    require(meta.get("licenses", {}).get("status") == "PENDING" and
            meta["licenses"].get("distribution_approved") is False,
            "this diagnostic path assumes an unapproved prototype")
    variant = meta.get("variant")
    require(variant in {"male", "female"}, "invalid avatar variant")
    avatar_glb = avatar / "avatar.glb"
    require(avatar_glb.is_file() and
            hashfile(avatar_glb) == meta["file_sha256"]["avatar.glb"],
            "avatar GLB sha256 mismatch")
    # Preserve the untouched Microsoft MIT license next to every derived GLB.
    notice = avatar / "UPSTREAM_LICENSE.md"
    require(notice.is_file() and hashfile(notice) ==
            meta.get("licenses", {}).get("original_notice_sha256"),
            "source avatar cannot be redistributed without exact Microsoft MIT NOTICE")
    output.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(notice, output / "UPSTREAM_LICENSE.md")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(avatar_glb))
    rig, mesh = _find_real_skin()
    # Render GLB REST before pose transfer to isolate skin bind problems.
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    rest_vertices = _sample_skin_vertices(mesh)
    _studio(mesh, rig)
    rest_image = output / "imported_glb_rest.png"
    scene.render.filepath = str(rest_image)
    bpy.ops.render.render(write_still=True)
    # Calibrate ONE rigid source-to-rig basis, then preserve OBSERVED
    # anatomical segment directions. The previous per-bone reference-relative
    # swings zeroed out independently bent knees/elbows at the chosen sample,
    # changing joint flexion and compounding non-anatomical articulation.
    # Camera alignment does NOT imply a validated world/root calibration.
    reference = choose_reference(captured)
    align = infer_alignment([reference], rig)
    rest_dirs = {
        name: direction(rig.data.bones[name].head_local,
                        rig.data.bones[name].tail_local)
        for name, _, _ in BONE_TARGETS
    }
    # A fixed hip/root makes a squat's feet intersect the ground as the
    # knees bend. With monocular hip-relative observations we cannot recover
    # the true absolute root; solve only a local VERTICAL support correction.
    # This uses genuine reconstructed foot directions, not a synthetic motion.
    rig.location.z = 0.0
    bpy.context.view_layer.update()
    rest_foot_floor_z = min(
        (rig.matrix_world @ rig.pose.bones[name].tail).z
        for name in ("Bip01 L Foot", "Bip01 R Foot")
    )
    def rig_space_diagnostic(stage, frame):
        """Observe the FBX imported scale/rest/model matrices BEFORE any fix."""
        bpy.context.view_layer.update()
        items = []
        for name in ("Bip01 Pelvis", "Bip01 Spine", "Bip01 L Thigh",
                     "Bip01 L Calf", "Bip01 L Foot", "Bip01 R Foot"):
            bone = rig.pose.bones[name]
            a = rig.matrix_world @ bone.head
            b = rig.matrix_world @ bone.tail
            items.append({
                "name": name,
                "length_local": round(bone.length, 4),
                "head_local": [round(float(x),4) for x in bone.head],
                "head_world": [round(float(x),4) for x in a],
                "tail_world": [round(float(x),4) for x in b],
                "translation": [round(float(x),5) for x in bone.location],
                "rotation": [round(float(x),5) for x in bone.rotation_quaternion],
            })
        report = {
            "stage": stage, "frame": frame,
            "rig_object_scale": [round(float(x),5) for x in rig.scale],
            "mesh_object_scale": [round(float(x),5) for x in mesh.scale],
            "rig_world_scale": [round(float(x),5)
                                for x in rig.matrix_world.to_scale()],
            "rig_world_translation": [round(float(x),5)
                                       for x in rig.matrix_world.translation],
            "mesh_world_scale": [round(float(x),5)
                                 for x in mesh.matrix_world.to_scale()],
            "rest_foot_floor_z": round(float(rest_foot_floor_z), 5),
            "bones": items,
        }
        print("EMS_G1_RIG_SPACE_DIAG=" + json.dumps(report))
        return report
    rig_space_diagnostic("IMPORTED_GLTF_BEFORE_RETARGET", 0)
    previous_root_z = 0.0
    support_anchors = []
    support_held_frames = 0
    maximum_root_vertical_displacement = 0.0
    last_safe_dirs = {}
    last_safe_timestamps = {}
    low_visibility_holds = 0
    temporal_swing_clamps = 0
    # A rate limit is a temporal constraint, not a limit per output frame.
    # Reappearance after a long occlusion gets the actual elapsed time to
    # reacquire the observed direction rather than remaining frozen.
    maximum_allowed_speed_deg_s = 330.0

    first_ms = stamps[0]
    last_frame_number = 0
    last_observed = None
    held_missing: list[int] = []
    peak_angular_error = 0.0
    peak_twist_error = 0.0
    scene = bpy.context.scene
    scene.render.fps = fps
    mapped = [(rig.pose.bones[name], p, c) for name, p, c in BONE_TARGETS]
    for sample in frames_all:
        t = sample["timestamp_ms"]
        fno = 1 + round((t - first_ms) * fps / 1000)
        require(fno > last_frame_number, "frame timestamps collide at requested fps")
        last_frame_number = fno
        scene.frame_set(fno)
        # Prevent last frame's animated root transform from contaminating
        # the next frame's local ground-relative estimate.
        rig.location.z = 0.0
        for posebone, _, _ in mapped:
            posebone.rotation_mode = "QUATERNION"
            posebone.rotation_quaternion = (1, 0, 0, 0)
            posebone.location = (0, 0, 0)
            posebone.scale = (1, 1, 1)
        bpy.context.view_layer.update()

        observed_now = sample.get("state") == "SOLVED_REVIEW_REQUIRED"
        if observed_now:
            last_observed = sample
        else:
            # Hold the last OBSERVED pose explicitly through occlusion. This is
            # an unmeasured frame, NOT a newly invented capture result.
            held_missing.append(t)
        if last_observed is None:
            continue
        p = {name: align @ from_solved(vec)
             for name, vec in last_observed["joints"].items()}
        unreliable = {
            flag["segment"] for flag in
            last_observed.get("unreliable_segments", [])
        }
        for posebone, parent, child in mapped:
            name = posebone.name
            if not observed_now or child in unreliable:
                # A missing frame is never counted as a fresh observation.
                # Unreliable segments HOLD the last known safe direction.
                if observed_now:
                    low_visibility_holds += 1
                expected = last_safe_dirs.get(name, rest_dirs[name])
            else:
                expected = direction(p[parent], p[child])
                if name in last_safe_dirs:
                    previous = last_safe_dirs[name]
                    dt_s = (t - last_safe_timestamps[name]) / 1000.0
                    require(dt_s > 0, "non-monotonic reliable segment timestamp")
                    allowed = maximum_allowed_speed_deg_s * dt_s
                    step_deg = math.degrees(previous.angle(expected))
                    if step_deg > allowed:
                        temporal_swing_clamps += 1
                        expected = previous.slerp(expected, allowed / step_deg)
                # First visible observation has no previous measured pose:
                # do NOT clamp it from the avatar's unrelated bind rest.
                last_safe_dirs[name] = expected
                last_safe_timestamps[name] = t
            if name in _SPINE_BLEND:
                # The current bone direction includes the preceding parent
                # swing. Progressively aim one third of the remaining torso
                # angle in each spinal segment. No synthetic observation is
                # introduced: the shared desired orientation comes from
                # the same real MediaPipe pelvis->chest measurement.
                current_spine = direction(posebone.head, posebone.tail)
                angle_to_target = current_spine.angle(expected)
                if angle_to_target > 1e-6:
                    expected = current_spine.slerp(
                        expected, _SPINE_BLEND[name]
                    ).normalized()
            err, twist_err = _set_global_direction(posebone, expected)
            peak_angular_error = max(peak_angular_error, err)
            peak_twist_error = max(peak_twist_error, twist_err)
        # The lower VISIBLE toe approximates a support anchor; when both toes
        # are occluded or the frame is absent, HOLD the previous estimate.
        # This does not solve horizontal foot locks or prove actual contact.
        good_feet = []
        if sample.get("state") == "SOLVED_REVIEW_REQUIRED":
            if not ({"leftToe", "leftAnkle"} & unreliable):
                good_feet.append("Bip01 L Foot")
            if not ({"rightToe", "rightAnkle"} & unreliable):
                good_feet.append("Bip01 R Foot")
        bpy.context.view_layer.update()
        if good_feet:
            lowest_toe_z = min(
                (rig.matrix_world @ rig.pose.bones[name].tail).z
                for name in good_feet
            )
            previous_root_z = rest_foot_floor_z - lowest_toe_z
            maximum_root_vertical_displacement = max(
                maximum_root_vertical_displacement, abs(previous_root_z)
            )
        else:
            support_held_frames += 1
        if fno in (1, 10, 25, 46):
            rig_space_diagnostic("AFTER_SWING_BEFORE_ROOT", fno)
            print("EMS_G1_ROOT_SUPPORT_DEBUG=" + json.dumps({
                "frame": fno, "root_vertical_m": previous_root_z,
                "support_feet": good_feet,
                "rest_floor": rest_foot_floor_z,
            }))
        rig.location.z = previous_root_z
        bpy.context.view_layer.update()
        support_anchors.append({
            "frame": fno,
            "valid": bool(good_feet),
            "observed_feet": good_feet,
            "applied_root_z_m": round(previous_root_z, 7),
        })
        rig.keyframe_insert(data_path="location", frame=fno)
        for posebone, _, _ in mapped:
            posebone.keyframe_insert(data_path="rotation_quaternion", frame=fno)

    scene.frame_start = 1
    scene.frame_end = last_frame_number
    require(rig.animation_data is not None and
            rig.animation_data.action is not None,
            "no genuine armature animation recorded")
    for action in bpy.data.actions:
        if hasattr(action, "fcurves"):
            for curve in action.fcurves:
                for key in curve.keyframe_points:
                    key.interpolation = "LINEAR"

    # Measure deformation at the camera-alignment reference frame. It is
    # NOT a neutral/rest pose and no small-distance assertion is justified.
    neutral_fno = 1 + round((reference["timestamp_ms"] - first_ms)
                           * fps / 1000)
    scene.frame_set(neutral_fno)
    bpy.context.view_layer.update()
    reference_vertices = _sample_skin_vertices(mesh)
    require(len(rest_vertices) == len(reference_vertices),
            "mesh topology changed during retarget")
    neutral_rest_deviation_m = max(
        math.dist(a, b) for a, b in zip(rest_vertices, reference_vertices)
    )
    scene.frame_set(1)
    editable = output / "retarget_review.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(editable))
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    glb = output / "retarget_review.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(glb), export_format="GLB",
        use_selection=True, export_skins=True, export_animations=True,
        export_cameras=False, export_lights=False,
        export_animation_mode="ACTIVE_ACTIONS",
    )
    require(glb.is_file() and glb.stat().st_size > 100_000,
            "animated skinned avatar GLB export failed")

    bpy.ops.object.select_all(action="DESELECT")
    frame_folder = output / "frames"
    frame_folder.mkdir(parents=True, exist_ok=True)
    samples = sorted({
        1 + round(i * (last_frame_number - 1) / 7)
        for i in range(8)
    })
    for index, fno in enumerate(samples):
        scene.frame_set(fno)
        scene.render.filepath = str(frame_folder / f"frame_{index:03d}.png")
        bpy.ops.render.render(write_still=True)
    png = output / "retarget_review.png"
    shutil.copyfile(frame_folder / "frame_004.png", png)
    shutil.copyfile(attribution, output / "SOURCE_ATTRIBUTION.txt")

    manifest = {
        "schema_version": "0.1.0",
        "data_type": "SKINNED_HUMAN_RETARGET_DIAGNOSTIC_NOT_FINAL_MOTION",
        "status": "REVIEW_REQUIRED",
        "variant": variant,
        "rig_profile": "ems.humanoid.rocketbox.sports.v1",
        "rig_bones": len(rig.data.bones),
        "avatar_source_license": "MIT",
        "avatar_source_license_file": "UPSTREAM_LICENSE.md",
        "avatar_source_license_sha256": hashfile(output / "UPSTREAM_LICENSE.md"),
        "animated_bones": len(BONE_TARGETS),
        "method": "REAL_CAPTURE_SEGMENT_DIRECTION_RETARGET",
        "spine_swing_strategy": "PROGRESSIVE_THREE_SEGMENT_ALLOCATION",
        "head_orientation": "NOT_OBSERVED_NECK_FOLLOWS_TORSO",
        "strategy": "SHARED_BASIS_OBSERVED_DIRECTIONS_UNCALIBRATED",
        "reference_timestamp_ms": reference["timestamp_ms"],
        "reference_selection": "MOST_UPRIGHT_OBSERVED_CAMERA_ALIGNMENT_ONLY",
        "reference_pose_bind_mesh_deviation_m": round(neutral_rest_deviation_m, 6),
        "rest_mesh_preview": "imported_glb_rest.png",
        "low_visibility_bone_holds": low_visibility_holds,
        "temporal_swing_clamps": temporal_swing_clamps,
        "swing_angular_speed_limit_deg_per_s": maximum_allowed_speed_deg_s,
        "foot_support_strategy": "VISIBLE_LOWEST_TOE_VERTICAL_ONLY_UNCALIBRATED",
        "rest_foot_anchor_z_m": round(rest_foot_floor_z, 7),
        "support_root_animation": support_anchors,
        "support_frames_held": support_held_frames,
        "maximum_vertical_root_correction_m": round(
            maximum_root_vertical_displacement, 6
        ),
        "original_video_sha256": raw["source_sha256"],
        "pose_model_sha256": raw["model_sha256"],
        "solved_skeleton_sha256": hashfile(source),
        "avatar_source_glb_sha256": hashfile(avatar_glb),
        "source_video_license": "CC-BY-SA-4.0",
        "derivative_distribution_terms": "CC-BY-SA-4.0",
        "source_attribution_file": "SOURCE_ATTRIBUTION.txt",
        "sample_fps": fps,
        "source_frames": len(frames_all),
        "detected_frames": len(captured),
        "timeline_end_frame": last_frame_number,
        "missing_or_ambiguous_timestamps_ms": held_missing,
        "maximum_bone_alignment_error_degrees": round(peak_angular_error, 5),
        "maximum_unobserved_twist_error_degrees": round(peak_twist_error, 5),
        "outputs": {
            "editable": "retarget_review.blend",
            "glb": "retarget_review.glb",
            "png": "retarget_review.png",
            "rest_png": "imported_glb_rest.png",
            "webp": "NOT_GENERATED",
        },
        "rights_review": "PENDING",
        "human_visual_review": "PENDING",
        "biomechanics_review": "PENDING",
        "full_body_ik": "NOT_IMPLEMENTED",
        "absolute_root_motion": "NOT_OBSERVABLE",
        "hand_grips": "NOT_SOLVED",
        "foot_contacts": "VERTICAL_SUPPORT_ESTIMATE_ONLY_NO_IK_OR_SLIDING_LOCK",
        "license_separation": "ROCKETBOX_MIT_MESH_PLUS_WIKIMEDIA_CC_BY_SA_MOTION",
        "bone_twist": "NOT_OBSERVABLE",
        "commercial_approval": False,
        "qa_gate_g1": "NOT_APPROVED",
        "file_sha256": {
            name: hashfile(output / name)
            for name in ("retarget_review.blend",
                         "retarget_review.glb",
                         "retarget_review.png",
                         "imported_glb_rest.png",
                         "SOURCE_ATTRIBUTION.txt",
                         "UPSTREAM_LICENSE.md")
        },
    }
    (output / "retarget_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("EMS_REAL_HUMAN_RETARGET=" + json.dumps({
        "variant": variant,
        "glb_bytes": glb.stat().st_size,
        "captured_frames": len(captured),
        "mapped_bones": len(BONE_TARGETS),
        "maximum_bone_alignment_error_degrees": round(peak_angular_error, 5),
        "maximum_unobserved_twist_error_degrees": round(peak_twist_error, 5),
        "reference_pose_bind_mesh_deviation_m": round(neutral_rest_deviation_m, 6),
        "missing_frames_held_for_review": len(held_missing),
        "low_visibility_bone_holds": low_visibility_holds,
        "temporal_swing_clamps": temporal_swing_clamps,
        "vertical_root_anchor_held_frames": support_held_frames,
        "max_vertical_root_correction_m": round(
            maximum_root_vertical_displacement, 6
        ),
        "human_visual_review": "PENDING",
        "commercial_approval": False,
    }))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap.add_argument("--solved", type=Path, required=True)
    ap.add_argument("--avatar-dir", type=Path, required=True)
    ap.add_argument("--attribution", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--fps", type=int, default=6)
    opts = ap.parse_args(args)
    generate(opts.solved.resolve(strict=True),
             opts.avatar_dir.resolve(strict=True),
             opts.output_dir.resolve(),
             opts.attribution.resolve(strict=True), opts.fps)
