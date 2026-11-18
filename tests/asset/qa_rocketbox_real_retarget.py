"""Headless Blender proof of animated skin deformation in a REAL-video retarget.

Does NOT certify anatomical correctness, bone twist, rooting, contact or legal
distribution. On false-pass conditions stop and leave G1 IN_PROGRESS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for chunk in iter(lambda: inp.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require(ok, reason):
    if not ok:
        raise AssertionError(reason)


def skin_sample(mesh, rig, frame):
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    dep = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh.evaluated_get(dep)
    geo = evaluated.to_mesh()
    try:
        step = max(1, len(geo.vertices) // 400)
        return [
            tuple(mesh.matrix_world @ geo.vertices[i].co)
            for i in range(0, len(geo.vertices), step)
        ]
    finally:
        evaluated.to_mesh_clear()




def glb_first_animation_key_seconds(glb_path: Path) -> float:
    """Read actual glTF 2.0 animation timestamps, not assumed Blender FPS.

    A 1-based Blender key at frame 1 was exported at 1/fps rather than at
    zero. Imported GLB and editable .blend therefore have different start
    offsets as well as different scene frame rates. Extract the time base
    directly from the GLB accessor minima to avoid false joint/floor QA.
    """
    with glb_path.open("rb") as stream:
        header = stream.read(20)
        require(len(header) == 20, "truncated GLB header")
        magic, version, total_bytes, json_length, chunk_type = struct.unpack(
            "<IIIII", header
        )
        require(magic == 0x46546C67 and version == 2,
                "not a glTF 2.0 binary")
        require(chunk_type == 0x4E4F534A and
                0 < json_length <= 10 * 1024 * 1024 and
                total_bytes == glb_path.stat().st_size,
                "invalid GLB JSON chunk")
        document = json.loads(stream.read(json_length))
    animations = document.get("animations", [])
    require(len(animations) >= 1, "GLB has no animation")
    accessors = document.get("accessors", [])
    first_keys = []
    for animation in animations:
        for sampler in animation.get("samplers", []):
            idx = sampler.get("input")
            require(type(idx) is int and 0 <= idx < len(accessors),
                    "invalid glTF sampler input accessor")
            acc = accessors[idx]
            low = acc.get("min")
            require(isinstance(low, list) and len(low) == 1 and
                    type(low[0]) in (int, float) and
                    math.isfinite(low[0]) and low[0] >= 0,
                    "missing or invalid glTF animation timestamp minimum")
            first_keys.append(float(low[0]))
    require(first_keys, "no timestamped GLB animation samplers")
    first = min(first_keys)
    require(first < .5,
            "unexpectedly delayed GLB first key: " + str(first))
    return first


def frame_from_capture(source_frame, report, *, origin_seconds=0.0):
    """Map captured frame index to the current Blender scene timebase.

    Blender .blend preserves authored 6fps; glTF import normally starts
    with scene-default 24fps. GLB animation uses seconds; sampling the
    original frame indices at 24fps falsely compares different instants.
    """
    original_fps = report["sample_fps"]
    scene = bpy.context.scene
    current_fps = scene.render.fps / scene.render.fps_base
    require(type(source_frame) is int and source_frame >= 1,
            "source frame index invalid")
    require(type(original_fps) in (int, float) and
            math.isfinite(original_fps) and original_fps > 0,
            "invalid source timebase")
    require(math.isfinite(current_fps) and current_fps > 0,
            "invalid imported scene timebase")
    require(math.isfinite(origin_seconds) and 0 <= origin_seconds < .5,
            "invalid animation start offset")
    if origin_seconds > 0.0:
        # glTF timestamps map to Blender frame = round(seconds * fps);
        # Blender frame indices are already 1-based at the source. Adding
        # 1 here was a one-frame phase shift after import (bone angles
        # and grounded-toe positions were measured at the wrong instant).
        return round(((source_frame - 1) / original_fps +
                      origin_seconds) * current_fps)
    return 1 + round((source_frame - 1) * current_fps / original_fps)


# Rocketbox FBX edit-bone tails created by glTF import can be MANY metres
# away from their true children. Use actual child bone HEAD joint centers.
JOINT_ENDPOINT = {
    "Bip01 L UpperArm": "Bip01 L Forearm",
    "Bip01 R UpperArm": "Bip01 R Forearm",
    "Bip01 L Forearm": "Bip01 L Hand",
    "Bip01 R Forearm": "Bip01 R Hand",
    "Bip01 L Thigh": "Bip01 L Calf",
    "Bip01 R Thigh": "Bip01 R Calf",
    "Bip01 L Calf": "Bip01 L Foot",
    "Bip01 R Calf": "Bip01 R Foot",
    "Bip01 L Foot": "Bip01 L Toe0",
    "Bip01 R Foot": "Bip01 R Toe0",
}
ANIMATED = {
    "Bip01 Spine", "Bip01 Spine1", "Bip01 Spine2",
    "Bip01 L Clavicle", "Bip01 R Clavicle",
    "Bip01 L UpperArm", "Bip01 L Forearm",
    "Bip01 R UpperArm", "Bip01 R Forearm",
    "Bip01 L Thigh", "Bip01 L Calf",
    "Bip01 R Thigh", "Bip01 R Calf",
    "Bip01 L Foot", "Bip01 R Foot", "Bip01 Neck",
}


def measured_joint_attachment(rig, last_frame):
    """True glTF articulated skeleton: check segment length invariance in METRES.

    A glTF-imported Blender edit-bone.tail may point to an unrelated inferred
    endpoint and is NOT a human joint. True parent/child heads in the glTF
    node hierarchy are actual anatomical joints. Preserve segment lengths
    over the FULL animation; do not invent joint-gap measurements.
    """
    require(all(name in rig.pose.bones for name in
                {*ANIMATED, *JOINT_ENDPOINT.values()}),
            "missing actual anatomical linked bone heads")
    base = {}
    peak_delta = 0.0
    peak_relative = 0.0
    worst = None
    max_local_translation = 0.0
    for fno in range(1, last_frame + 1):
        bpy.context.scene.frame_set(fno)
        bpy.context.view_layer.update()
        for parent, child in JOINT_ENDPOINT.items():
            # Blender armature object carries inherited FBX unit conversion,
            # so convert BOTH joint HEADS into world metres before distance.
            a = rig.matrix_world @ rig.pose.bones[parent].head
            b = rig.matrix_world @ rig.pose.bones[child].head
            distance = (a-b).length
            require(math.isfinite(distance) and .02 <= distance <= .9,
                    "out-of-range actual human segment length: " +
                    f"{parent}->{child} at frame {fno}={distance:.4f}m")
            if parent not in base:
                base[parent] = distance
            delta = abs(distance - base[parent])
            relative = delta / base[parent]
            if relative > peak_relative:
                peak_relative = relative
                peak_delta = delta
                worst = {"frame": fno, "segment": parent + "->" + child,
                         "initial_length_m": round(base[parent], 6),
                         "current_length_m": round(distance, 6)}
        for name in ANIMATED:
            distance = rig.pose.bones[name].location.length
            require(math.isfinite(distance), "nonfinite deform bone translation")
            max_local_translation = max(max_local_translation, distance)
    require(peak_relative <= .01,
            f"actual human segment changed length more than 1%: {worst} "
            f"delta={peak_relative:.6%}")
    require(max_local_translation <= .001,
            "deform bones acquired local translation beyond 1mm")
    return {
        "status": "SEGMENT_LENGTH_TECHNICAL_PASS",
        "reference": "PARENT_HEAD_TO_ACTUAL_CHILD_HEAD_IN_WORLD_METRES",
        "max_segment_length_deviation_m": round(peak_delta, 7),
        "max_segment_length_relative_deviation": round(peak_relative, 7),
        "max_nonroot_bone_translation_m": round(max_local_translation, 7),
        "worst": worst,
        "checked_frames": last_frame,
        "commercial_approval": False,
    }


def measured_kinematic_fidelity(
    rig, solved, report, *, origin_seconds=0.0
):
    """Independently compare original solved REAL-video joint angles with the
    exported GLB's animated pose bones after roundtrip. This is a screening
    test, not evidence of absolute scene/pose or commercial correctness."""
    require(hash_path(solved) == report["solved_skeleton_sha256"],
            "QA must use the exact source solved skeleton of this GLB")
    raw = json.loads(solved.read_text(encoding="utf-8"))
    require(raw.get("data_type") == "INTERMEDIATE_SKELETON_NOT_FINAL_MOTION",
            "joint QA requires real intermediate skeleton provenance")
    frames = raw["frames"]
    first_ms = frames[0]["timestamp_ms"]
    joints = (
        ("leftElbow", "leftShoulder", "leftElbow", "leftWrist",
         "Bip01 L UpperArm", "Bip01 L Forearm"),
        ("rightElbow", "rightShoulder", "rightElbow", "rightWrist",
         "Bip01 R UpperArm", "Bip01 R Forearm"),
        ("leftKnee", "leftHip", "leftKnee", "leftAnkle",
         "Bip01 L Thigh", "Bip01 L Calf"),
        ("rightKnee", "rightHip", "rightKnee", "rightAnkle",
         "Bip01 R Thigh", "Bip01 R Calf"),
    )
    fps = report["sample_fps"]
    limit_deg = 15.0  # screening threshold only, NOT a tuned approval gate
    errors = []
    alerts = []
    per_joint = {group[0]: [] for group in joints}
    for sample in frames:
        if sample.get("state") != "SOLVED_REVIEW_REQUIRED":
            continue
        source_frame = 1 + round(
            (sample["timestamp_ms"] - first_ms) * fps / 1000
        )
        frame_no = frame_from_capture(
            source_frame, report, origin_seconds=origin_seconds
        )
        require(1 <= source_frame <= report["timeline_end_frame"],
                "solved timestamp does not match GLB animation timeline")
        bpy.context.scene.frame_set(frame_no)
        bpy.context.view_layer.update()
        omitted = {x["segment"] for x in sample.get("unreliable_segments", [])}
        xyz = sample["joints"]
        for key, parent, middle, child, bone_a, bone_b in joints:
            if middle in omitted or child in omitted:
                continue
            source_upper = Vector(xyz[middle]) - Vector(xyz[parent])
            source_lower = Vector(xyz[child]) - Vector(xyz[middle])
            require(source_upper.length > .00001 and source_lower.length > .00001,
                    "degenerate real source joint under angular QA")
            source_angle = math.degrees(source_upper.angle(source_lower))
            upper = rig.pose.bones[bone_a]
            lower = rig.pose.bones[bone_b]
            # Bone tails reconstructed by Blender from imported glTF are
            # arbitrary; glTF source joints are actual CHILD HEAD positions.
            actual_upper = lower.head - upper.head
            lower_end = rig.pose.bones[JOINT_ENDPOINT[bone_b]]
            actual_lower = lower_end.head - lower.head
            require(actual_upper.length > .00001 and actual_lower.length > .00001,
                    "degenerate exported GLB joint geometry")
            output_angle = math.degrees(actual_upper.angle(actual_lower))
            error = abs(output_angle - source_angle)
            require(math.isfinite(error), "nonfinite reimported GLB joint angle")
            errors.append(error)
            per_joint[key].append(error)
            if error > limit_deg:
                alerts.append({
                    "timestamp_ms": sample["timestamp_ms"],
                    "joint": key,
                    "source_flexion_degrees": round(source_angle, 3),
                    "glb_flexion_degrees": round(output_angle, 3),
                    "error_degrees": round(error, 3),
                })
    require(len(errors) >= 12,
            "insufficient visible real elbow/knee observations for GLB QA")
    return {
        "status": "FAIL_REVIEW_REQUIRED" if alerts else "SCREENING_PASS_NOT_FINAL_QA",
        "screening_limit_degrees": limit_deg,
        "observed_joint_frame_pairs": len(errors),
        "max_flexion_error_degrees": round(max(errors), 4),
        "mean_flexion_error_degrees": round(sum(errors)/len(errors), 4),
        "joint_max_error_degrees": {
            key: round(max(samples), 4) if samples else None
            for key, samples in per_joint.items()
        },
        "review_event_count": len(alerts),
        "review_events_first_25": alerts[:25],
        "provenance": "SOURCE_SOLVED_SKELETON_VERSUS_GLTF_REIMPORTED_SKIN",
        "limitations": "No absolute root, depth certainty, contact, twist, collision or visual approval",
    }


def hash_path(path):
    return sha(path)

def measure_vertical_support(
    rig, anchors, report, floor_z, *, origin_seconds=0.0
):
    """Measure support at exactly matching ANIMATION SECONDS in this scene.

    Record rather than bypass failed values. Called on imported GLB and then
    independently on the original editable .blend to isolate export drift.
    """
    largest = 0.0
    worst_frame = None
    checked = 0
    for anchor in anchors:
        require(type(anchor.get("frame")) is int and
                type(anchor.get("valid")) is bool,
                "invalid support metadata")
        feet = anchor.get("observed_feet")
        require(isinstance(feet, list) and
                set(feet).issubset({"Bip01 L Foot", "Bip01 R Foot"}) and
                bool(feet) == anchor["valid"],
                "invalid observed foot declaration")
        if not feet:
            continue
        scene_frame = frame_from_capture(
            anchor["frame"], report, origin_seconds=origin_seconds
        )
        bpy.context.scene.frame_set(scene_frame)
        bpy.context.view_layer.update()
        toe_z = min(
            (rig.matrix_world @ rig.pose.bones[JOINT_ENDPOINT[name]].head).z
            for name in feet
        )
        error = abs(toe_z - floor_z)
        require(math.isfinite(error), "nonfinite foot-support error")
        if error > largest:
            largest = error
            worst_frame = {"source_frame": anchor["frame"],
                           "scene_frame": scene_frame,
                           "feet": feet,
                           "error_m": round(error, 7)}
        checked += 1
    require(checked >= 3,
            "not enough visible foot anchors for review")
    return {"max_error_m": round(largest, 7),
            "worst": worst_frame, "observed_frames": checked,
            "scene_fps": bpy.context.scene.render.fps /
                         bpy.context.scene.render.fps_base}


def measure_inferred_toe_xy_lock(
    rig, anchors, report, *, origin_seconds=0.0
):
    """Independent XYZ-contact-hypothesis check after real GLB reimport.

    Only explicitly declared/visible source-ground hypotheses count. Holds,
    alternations and unknown floor contact do not count as valid samples.
    A locked joint must match its constant source-anchor in WORLD metres,
    not just remain stationary in parent armature coordinates.
    """
    require(report.get("foot_support_strategy") ==
            "DOMINANT_TOE_XYZ_HYPOTHESIS_WITH_VERTICAL_FALLBACK",
            "wrong source contact hypothesis contract")
    inference = report.get("support_inference", {})
    support_foot = report.get("inferred_support_foot")
    anchor = report.get("inferred_toe_anchor_world_xyz_m")
    require(inference.get("ground_truth_contact") is False,
            "source toes cannot certify observed ground truth")
    require((support_foot is None and anchor is None) or
            (support_foot in {"Bip01 L Foot", "Bip01 R Foot"} and
             isinstance(anchor, list) and len(anchor) == 3 and
             all(type(x) in (int, float) and math.isfinite(x) for x in anchor)),
            "invalid support foot or anchor")
    require(all(item.get("hypothesis_not_ground_truth") is True
                for item in anchors), "support evidence misrepresents certainty")
    if support_foot is None:
        require(not any(a.get("support_lock_valid") for a in anchors),
                "ambiguous input must not silently create contact")
        return {"status": "AMBIGUOUS_REVIEW_REQUIRED",
                "checked_locked_frames": 0, "max_xy_contact_drift_m": None,
                "ground_truth_contact": False}
    target = Vector(anchor)
    errors = []
    worst = None
    for sample in anchors:
        if not sample.get("support_lock_valid"):
            continue
        require(sample.get("inferred_support_toe") == support_foot
                and sample.get("valid") is True
                and sample.get("observed_feet") == [support_foot],
                "locked support provenance differs from observed foot")
        source_frame = sample["frame"]
        bpy.context.scene.frame_set(frame_from_capture(
            source_frame, report, origin_seconds=origin_seconds
        ))
        bpy.context.view_layer.update()
        current_world = (
            rig.matrix_world @
            rig.pose.bones[JOINT_ENDPOINT[support_foot]].head
        )
        xy_drift = math.hypot(
            current_world.x - target.x,
            current_world.y - target.y,
        )
        require(math.isfinite(xy_drift),
                "nonfinite world support-toe distance")
        errors.append(xy_drift)
        if worst is None or xy_drift > worst["distance_m"]:
            worst = {"source_frame": source_frame,
                     "distance_m": round(xy_drift, 8)}
    require(len(errors) == report["inferred_support_locked_frames"],
            "lost or fabricated actual locked frame count")
    require(len(errors) >= 3,
            "dominant toe lock had no genuine observed support")
    worst_error = max(errors)
    require(worst_error <= .03,
            "inferred grounded toe GLB X/Y drift exceeds 3cm: " +
            str(worst))
    return {
        "status": "TECHNICAL_INFERRED_TOE_LOCK_PASS_NOT_TRUE_CONTACT",
        "checked_locked_frames": len(errors),
        "max_xy_contact_drift_m": round(worst_error, 8),
        "worst": worst,
        "ground_truth_contact": False,
    }


def evaluate_real_mesh_camera_coverage(report):
    """Inspect the exact animated .blend skinned verts against saved camera.

    No screenshot checksum alone can prove feet are in the viewport. Test
    actual evaluated vertices at the eight observed review-frame samples,
    in Blender camera NDC; this is not a substitute for biomechanical QA.
    """
    scene = bpy.context.scene
    cam = scene.camera
    require(cam is not None and cam.data.type == "ORTHO",
            "editable human source lacks an orthographic review camera")
    frames = report["actual_motion_camera_framing"]["frames"]
    require(len(frames) == 8, "expected eight independently framed source poses")
    mesh_candidates = [
        o for o in scene.objects if o.type == "MESH"
        and len(o.data.vertices) > 1000
        and any(mod.type == "ARMATURE" for mod in o.modifiers)
    ]
    require(mesh_candidates, "no real deformable human mesh in editable .blend")
    body = max(mesh_candidates, key=lambda o: len(o.data.vertices))
    bounds = []
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        evaluated = body.evaluated_get(dg)
        verts = evaluated.to_mesh()
        try:
            step = max(1, len(verts.vertices)//1000)
            coords = [
                world_to_camera_view(
                    scene, cam, body.matrix_world @ verts.vertices[i].co)
                for i in range(0,len(verts.vertices),step)
            ]
        finally:
            evaluated.to_mesh_clear()
        require(len(coords) >= 200, "insufficient captured human geometry")
        xs = [v.x for v in coords]
        ys = [v.y for v in coords]
        zs = [v.z for v in coords]
        frame_data = {
            "frame": frame,
            "min_u": round(min(xs),5), "max_u": round(max(xs),5),
            "min_v": round(min(ys),5), "max_v": round(max(ys),5),
            "closest_depth": round(min(zs),5),
        }
        bounds.append(frame_data)
        require(0.01 <= min(xs) and max(xs) <= .99 and
                .01 <= min(ys) and max(ys) <= .99 and min(zs) > 0,
                "actual moving human cropped by camera at frame " +
                str(frame_data))
    return {"status":"GEOMETRY_VIEWPORT_PASS_HUMAN_VISUAL_STILL_PENDING",
            "measured_frames":bounds}


def inspect(folder: Path, solved: Path):
    report = json.loads((folder / "retarget_manifest.json").read_text(
        encoding="utf-8"
    ))
    require(report["data_type"] == "SKINNED_HUMAN_RETARGET_DIAGNOSTIC_NOT_FINAL_MOTION",
            "not retarget output")
    require(report["method"] == "REAL_CAPTURE_SEGMENT_DIRECTION_RETARGET",
            "source provenance must be authentic video processing")
    require(report["commercial_approval"] is False and
            report["qa_gate_g1"] == "NOT_APPROVED",
            "unreviewed source cannot be approved by technical checks")
    require(report["source_video_license"] == "CC-BY-SA-4.0",
            "source license is missing")
    require(report.get("segment_geometry_reference") ==
            "PARENT_HEAD_TO_CHILD_HEAD_NOT_BONE_TAIL",
            "must never use invented glTF bone tails for human biomechanics")
    require(type(report.get("maximum_vertical_root_correction_m")) in (float, int)
            and report["maximum_vertical_root_correction_m"] < .85,
            "excessive human root correction: camera/scale/IK invalid")
    require(report["rig_profile"] == "ems.humanoid.rocketbox.sports.v1"
            and report.get("rig_bones") == 80,
            "human avatar must be an authentic Rocketbox 80-bone rig")
    require(report.get("avatar_source_license") == "MIT"
            and report.get("avatar_source_license_file") == "UPSTREAM_LICENSE.md",
            "Microsoft Rocketbox MIT source must be preserved")
    require((folder / "UPSTREAM_LICENSE.md").is_file()
            and sha(folder / "UPSTREAM_LICENSE.md") ==
            report.get("avatar_source_license_sha256"),
            "commercially redistributable base human lost exact MIT copyright")
    require(report["human_visual_review"] == "PENDING" and
            report["biomechanics_review"] == "PENDING",
            "cannot bypass human review")
    require(report["source_frames"] >= 3 and report["detected_frames"] >= 3,
            "not enough actual human samples")
    require(report["animated_bones"] >= 14,
            "no realistic coverage of major leg/arm bones")
    for name, checksum in report["file_sha256"].items():
        file = folder / name
        require(file.is_file() and file.stat().st_size > 100,
                "missing output " + name)
        require(sha(file) == checksum, "output modified since generation: " + name)
    require((folder / "retarget_review.png").stat().st_size > 10000,
            "render missing")
    image = bpy.data.images.load(str(folder / "retarget_review.png"),
                                 check_existing=False)
    require(tuple(image.size) == (512, 768), "wrong review preview size")
    sample_pixels = image.pixels
    count_colors = set()
    step = max(4, (len(sample_pixels) // 600 // 4) * 4)
    for i in range(0, len(sample_pixels) - 4, step):
        count_colors.add(tuple(round(float(v), 2)
                               for v in sample_pixels[i:i + 3]))
    require(len(count_colors) > 10, "blank/noninformative diagnostic image")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    glb_origin_seconds = glb_first_animation_key_seconds(
        folder / "retarget_review.glb"
    )
    bpy.ops.import_scene.gltf(filepath=str(folder / "retarget_review.glb"))
    rigs = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    require(len(rigs) == 1, "GLB roundtrip must preserve single humanoid rig")
    rig = rigs[0]
    require(len(rig.data.bones) == 80, "GLB Rocketbox 80-bone hierarchy lost")
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"
              and len(o.data.vertices) >= 1000 and any(
                  m.type == "ARMATURE" and m.object == rig
                  for m in o.modifiers
              )]
    require(len(meshes) >= 1, "imported GLB has no skinned body")
    body = max(meshes, key=lambda m: len(m.data.vertices))
    require(sum(bool(v.groups) for v in body.data.vertices) >= 1000,
            "real vertex skin weights missing")
    require(len(bpy.data.actions) > 0,
            "GLB contains no actual animation actions")
    require(rig.animation_data is not None,
            "armature imported without bound action")

    # Independently validate that the ground-relative root correction survived
    # the GLB export. This proves only vertical toe anchoring on visible samples,
    # NOT horizontal foot locking, full body IK or a commercially valid motion.
    anchors = report.get("support_root_animation")
    require(isinstance(anchors, list) and
            len(anchors) == report["source_frames"],
            "support root provenance missing or incomplete")
    floor_z = report.get("rest_foot_anchor_z_m")
    require(type(floor_z) in (int, float) and math.isfinite(floor_z),
            "invalid original rest-toe reference")
    require(report.get("foot_support_strategy") ==
            "DOMINANT_TOE_XYZ_HYPOTHESIS_WITH_VERTICAL_FALLBACK",
            "unexpected source-to-ground hypothesis")
    require(report.get("full_body_ik") == "NOT_IMPLEMENTED" and
            report["commercial_approval"] is False,
            "toe anchoring cannot establish complete contact or IK")
    glb_support = measure_vertical_support(
        rig, anchors, report, floor_z,
        origin_seconds=glb_origin_seconds
    )
    maximum_floor_error = glb_support["max_error_m"]
    validated_support_frames = glb_support["observed_frames"]
    glb_toe_lock = measure_inferred_toe_xy_lock(
        rig, anchors, report, origin_seconds=glb_origin_seconds
    )

    imported_scene_fps = (
        bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    )
    imported_end = frame_from_capture(
        report["timeline_end_frame"], report,
        origin_seconds=glb_origin_seconds
    )
    glb_first_frame = frame_from_capture(
        1, report, origin_seconds=glb_origin_seconds
    )
    joint_attachment = measured_joint_attachment(rig, imported_end)

    # Evaluate REAL deformed vertices of the SKINNED MESH, not root translations
    # or static posebones alone. Any nonzero pose must alter surface geometry.
    first = skin_sample(body, rig, 1)
    max_mesh_displacement = 0.0
    last = imported_end
    for fno in sorted({1, max(2, last // 4),
                       max(2, last // 2), max(2, last * 3 // 4),
                       last}):
        other = skin_sample(body, rig, fno)
        require(len(first) == len(other), "body topology changed over time")
        delta = max((math.dist(a, b) for a, b in zip(first, other)),
                    default=0.0)
        max_mesh_displacement = max(max_mesh_displacement, delta)
    require(max_mesh_displacement > .008,
            f"animated GLB has no genuine skin motion: {max_mesh_displacement}")

    # Check actual GLB joint flexion against original captured 3D directions.
    # This catches per-bone neutralization corrupting elbow/knee articulation
    # even when vertex animation, skins and GLB roundtrip technically pass.
    kinematic_fidelity = measured_kinematic_fidelity(
        rig, solved, report, origin_seconds=glb_origin_seconds
    )

    # Opening a different .blend destroys Blender RNA object references.
    # Retain scalar GLB evidence BEFORE that operation.
    glb_bones = len(rig.data.bones)
    glb_skin_weights = sum(bool(v.groups) for v in body.data.vertices)

    # Reopening the editable Blender project verifies it is more than a
    # glTF roundtrip. It must contain the actual rig with an action.
    bpy.ops.wm.open_mainfile(filepath=str(folder / "retarget_review.blend"))
    camera_coverage = evaluate_real_mesh_camera_coverage(report)
    edits = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    require(len(edits) == 1 and
            edits[0].animation_data and edits[0].animation_data.action,
            "editable Blender source lost animated skin")
    # Differential regression: establish whether wrong knee/elbow angles
    # are created during the Blender retarget or introduced by GLB export.
    # Compare the same SHA-pinned human observations at identical timestamps
    # against independently reloaded editable .blend and imported GLB.
    blend_scene_fps = (
        bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    )
    blend_support = measure_vertical_support(
        edits[0], anchors, report, floor_z
    )
    blend_toe_lock = measure_inferred_toe_xy_lock(
        edits[0], anchors, report
    )
    blend_fidelity = measured_kinematic_fidelity(edits[0], solved, report)
    require(blend_fidelity["observed_joint_frame_pairs"] ==
            kinematic_fidelity["observed_joint_frame_pairs"],
            "blend/GLB joint samples not comparable")
    flexion_export_drift = abs(
        blend_fidelity["max_flexion_error_degrees"] -
        kinematic_fidelity["max_flexion_error_degrees"]
    )
    result = {
        "technical_skinned_retarget": "PASS",
        "full_body_camera_coverage": camera_coverage,
        "variant": report["variant"],
        "source_frames": report["source_frames"],
        "actual_detected_frames": report["detected_frames"],
        "mapped_bones": report["animated_bones"],
        "glb_bones": glb_bones,
        "glb_skin_weights": glb_skin_weights,
        "real_mesh_deformation_span_m": round(max_mesh_displacement, 6),
        "joint_attachment": joint_attachment,
        "source_motion_fps": report["sample_fps"],
        "imported_glb_scene_fps": imported_scene_fps,
        "editable_blend_scene_fps": blend_scene_fps,
        "time_sampling_basis": "GLTF_ACCESSOR_START_SECONDS_AND_SCENE_FPS",
        "glb_first_animation_key_seconds": round(glb_origin_seconds, 7),
        "glb_first_animation_frame": glb_first_frame,
        "kinematic_fidelity": kinematic_fidelity,
        "editable_blend_kinematic_fidelity": blend_fidelity,
        "max_joint_flexion_export_drift_degrees": round(
            flexion_export_drift, 6
        ),
        "joint_angle_export_status": (
            "TECHNICAL_PASS" if flexion_export_drift <= 1.0
            else "FAIL_REVIEW_REQUIRED"
        ),
        "vertical_foot_anchor_roundtrip": (
            "TECHNICAL_PASS" if maximum_floor_error <= .03
            and blend_support["max_error_m"] <= .03
            else "FAIL_REVIEW_REQUIRED"
        ),
        "glb_vertical_support": glb_support,
        "blend_vertical_support": blend_support,
        "glb_inferred_toe_xy_lock": glb_toe_lock,
        "blend_inferred_toe_xy_lock": blend_toe_lock,
        "root_velocity_screening": {
            "status": "REVIEW_REQUIRED" if report.get(
                "root_speed_review_events") else "NO_OUTLIERS_OBSERVED",
            "max_m_per_second": report.get(
                "maximum_inferred_root_speed_m_s"),
            "review_event_count": len(report.get(
                "root_speed_review_events", [])),
            "ground_truth_root_motion": False,
        },
        "vertical_support_observed_frames": validated_support_frames,
        "vertical_support_held_frames": report["support_frames_held"],
        "maximum_vertical_foot_anchor_error_m": round(maximum_floor_error, 7),
        "human_visual_review": "PENDING",
        "biomechanics_review": "PENDING",
        "commercial_approval": False,
    }
    (folder / "retarget_qa.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print("EMS_REAL_SKINNED_GLB_QA=" + json.dumps(result))
    # Preserve both source and exported support evidence before failing closed.
    require(maximum_floor_error <= .03 and
            blend_support["max_error_m"] <= .03,
            "vertical toe support exceeds 3cm; compare .blend vs GLB "
            "in retarget_qa.json: " +
            str((glb_support, blend_support)))
    # Report and archive the failing differential before rejecting the run;
    # never convert a failed GLB into PASS merely to preserve evidence.
    require(flexion_export_drift <= 1.0,
            "GLB export changes joint flexion beyond 1 degree, "
            f"differential {flexion_export_drift:.5f}; "
            "see retarget_qa.json and actual render evidence")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--solved", type=Path, required=True)
    a = p.parse_args(args)
    inspect(a.output_dir.resolve(strict=True), a.solved.resolve(strict=True))
