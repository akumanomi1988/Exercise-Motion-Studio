"""Headless QA of genuine Rocketbox skinned GLB; not exercise/IK approval."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def skinned_vertices(mesh):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh.evaluated_get(depsgraph)
    data = evaluated.to_mesh()
    try:
        stride = max(1, len(data.vertices) // 512)
        return [tuple(mesh.matrix_world @ data.vertices[i].co)
                for i in range(0, len(data.vertices), stride)]
    finally:
        evaluated.to_mesh_clear()


def assert_embedded_gltf_textures(path: Path, variant: str):
    """Inspect the *binary* glTF buffers rather than Blender's image cache.

    A valid 2K texture in an exported GLB can be lazy/unloaded in bpy.images
    after import; image.has_data is not reliable as an embedded-data assertion.
    Confirm exact PNG headers, dimensions, material PBR binding and no 1x1
    fallback image. Confirm that rigged skin and all required maps are present.
    """
    data = path.read_bytes()
    require(len(data) > 10000, "GLB binary unexpectedly small")
    magic, version, declared = struct.unpack_from("<4sII", data, 0)
    require(magic == b"glTF" and version == 2 and declared == len(data),
            "invalid GLB binary header")
    chunk_len, chunk_type = struct.unpack_from("<II", data, 12)
    require(chunk_type == 0x4E4F534A, "GLB JSON chunk missing")
    doc = json.loads(data[20:20+chunk_len])
    buffer_start = 20 + chunk_len
    bin_len, bin_type = struct.unpack_from("<II", data, buffer_start)
    require(bin_type == 0x004E4942, "GLB embedded binary chunk missing")
    binary_start = buffer_start + 8
    require(binary_start + bin_len <= len(data), "GLB binary chunk out of bounds")
    views = doc.get("bufferViews", [])
    textures = doc.get("textures", [])
    images = doc.get("images", [])
    require(len(doc.get("skins", [])) == 1, "skin lost in binary GLB")
    require(len(images) >= (5 if variant == "female" else 4),
            "missing genuine body/head or cutout texture")
    image_names = set()
    for image in images:
        image_names.add(image.get("name", ""))
        require(image.get("mimeType") == "image/png"
                and isinstance(image.get("bufferView"), int),
                "external or unexpected unembedded glTF texture")
        view = views[image["bufferView"]]
        start = binary_start + view.get("byteOffset", 0)
        length = view["byteLength"]
        require(256 < length < bin_len
                and start >= binary_start
                and start + length <= binary_start + bin_len,
                "PNG texture bufferView outside binary glTF")
        payload = data[start:start+length]
        require(payload[:8] == b"\x89PNG\r\n\x1a\n"
                and payload[12:16] == b"IHDR",
                "actual glTF image buffer not PNG")
        width, height = struct.unpack_from(">II", payload, 16)
        require(width >= 1024 and height >= 1024,
                "GLB contains degraded/minified source texture")
    for kind in ("body_color", "body_normal", "head_color", "head_normal"):
        require(any(kind in n for n in image_names),
                "GLB missing pinned source " + kind)
    if variant == "female":
        require(any("opacity_color" in n for n in image_names),
                "GLB lacks female alpha cutout source texture")
    materials = doc.get("materials", [])
    relevant = [m for m in materials
                if any(part in m.get("name","").lower()
                       for part in ("body", "head", "opacity"))]
    require(len(relevant) >= (3 if variant == "female" else 2),
            "GLB missing expected human surface materials")
    for mat in relevant:
        tex = mat.get("pbrMetallicRoughness", {}).get("baseColorTexture", {})
        require(type(tex.get("index")) is int
                and 0 <= tex["index"] < len(textures),
                "genuine body/head/opacity PBR texture not bound")
    return {"embedded_texture_count": len(images),
            "material_count": len(relevant),
            "source_texture_resolution": "AT_LEAST_1024x1024"}


def inspect(source: Path, out: Path):
    src = json.loads((source / "source_provenance.json").read_text())
    report = json.loads((out / "import_report.json").read_text())
    require(src["license_spdx"] == report["license"] == "MIT",
            "third party source licence changed")
    require(not report["commercial_asset_approval"]
            and report["human_visual_approval"] == "PENDING",
            "no automated commercial approval permitted")
    for name, key in (("source.blend", "editable_blend_sha256"),
                      ("avatar.glb", "exported_glb_sha256"),
                      ("rest_review.png", "preview_png_sha256")):
        path = out / name
        require(path.is_file() and digest(path) == report[key],
                f"missing or altered real binary {name}")
    img = bpy.data.images.load(str(out / "rest_review.png"))
    require(tuple(img.size) == (512, 768),
            "real Blender review image has wrong dimensions")
    values = img.pixels
    stride = max(4, (len(values) // 400 // 4) * 4)
    require(len({tuple(round(float(v), 2) for v in values[i:i+3])
                 for i in range(0, len(values)-4, stride)}) >= 20,
            "avatar review image blank/uninformative")
    gltf_textures = assert_embedded_gltf_textures(
        out / "avatar.glb", report["variant"]
    )
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(out / "avatar.glb"))
    rigs = [x for x in bpy.context.scene.objects if x.type == "ARMATURE"]
    mesh = [x for x in bpy.context.scene.objects if x.type == "MESH" and
            len(x.data.vertices) > 1000 and any(
                mod.type == "ARMATURE" and mod.object in rigs
                for mod in x.modifiers)]
    require(rigs and mesh, "GLB lost real armature or deforming meshes")
    rig = max(rigs, key=lambda o: len(o.data.bones))
    require(len(rig.data.bones) == 80,
            "expected pinned 80-bone Rocketbox human skeleton, not placeholder")
    profile = json.loads(
        (Path(__file__).resolve().parents[2] /
         "assets/rig_profiles/rocketbox_sports_humanoid_v1.json").read_text(
            encoding="utf-8"
        )
    )
    require(report["source_avatar"] in profile["avatars"]
            and report["source_commit"] == profile["upstream_commit"],
            "human rig provenance differs from normalized profile")
    required = set(profile["bone_map"].values())
    actual = set(rig.data.bones.keys())
    require(required.issubset(actual),
            "glTF skeleton lost required canonical humanoid bones: " +
            repr(sorted(required - actual)))
    require(any(m.data.materials for m in mesh),
            "GLB has no attached source materials")
    body = max(mesh, key=lambda m: len(m.data.vertices))
    weights = sum(bool(v.groups) for v in body.data.vertices)
    require(weights > 1000, "GLB contains no usable skin weights")
    before = skinned_vertices(body)
    candidates = [b for b in rig.pose.bones if
                  ("arm" in b.name.lower() or "elbow" in b.name.lower())
                  and b.bone.use_deform]
    require(candidates, "no deforming arm bone for actual skinned motion test")
    chosen = max(candidates, key=lambda b: b.bone.length)
    chosen.rotation_mode = "QUATERNION"
    chosen.rotation_quaternion = Quaternion((0, 0, 1), .35)
    bpy.context.view_layer.update()
    after = skinned_vertices(body)
    require(len(before) == len(after), "animated skin sample sizes differ")
    deformation = max(math.dist(a, b) for a, b in zip(before, after))
    require(deformation > .002, "GLB skin does not actually deform under arm motion")
    require(math.isfinite(deformation) and deformation < 1.5,
            "unbounded skin deformation under simple bone movement")
    result = {
        "technical_glb_skeleton_and_skinning": "PASS",
        "variant": report["variant"],
        "source_avatar": report["source_avatar"],
        "bones": len(rig.data.bones),
        "shared_humanoid_profile": profile["profile_id"],
        "canonical_bones_mapped": len(profile["bone_map"]),
        "skinned_body_weighted_vertices": weights,
        "actual_deforming_bone": chosen.name,
        "actual_mesh_deformation_under_20deg_arm_swing_m": round(deformation, 6),
        "embedded_source_texture_count": gltf_textures["embedded_texture_count"],
        "binary_embedded_images_and_pbr": gltf_textures,
        "rest_png": "VISUAL_REVIEW_REQUIRED",
        "exercise_retarged_real_video": "NOT_TESTED",
        "contact_and_hand_ik": "NOT_TESTED",
        "commercial_approval": False,
    }
    (out / "qa_report.json").write_text(json.dumps(result, indent=2)+"\n")
    print("EMS_ROCKETBOX_GLTF_QA=" + json.dumps(result))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--source-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args(argv)
    inspect(a.source_dir.resolve(strict=True), a.output_dir.resolve(strict=True))
