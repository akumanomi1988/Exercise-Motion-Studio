"""Import genuine pinned Microsoft Rocketbox male/female sports avatars.

Produces diagnostic editable Blender, GLB and a rendered PNG from actual third-
party rigged/skinned characters. Does not perform motion capture or certify
retargeting. Licence remains MIT with original notice. Rejects missing skeleton
or skinning; no fake/procedural human is substituted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as reader:
        for block in iter(lambda: reader.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def attach_color_materials(source):
    """Rebuild all externally referenced FBX materials from SHA-pinned TGA.

    The original FBX stores absolute D:\\temp image paths. Importer creates
    unresolved linked images and the glTF exporter may emit 1x1 placeholders.
    Preserve actual Microsoft textures by replacing those broken shader nodes,
    including alpha cutout for the female hair/eyelashes geometry.
    """
    texture_dir = source / "Textures"
    roles = ("body_color", "head_color", "body_normal", "head_normal")
    textures = {name: sorted(texture_dir.glob("*_" + name + ".tga"))
                for name in roles}
    opacity_files = sorted(texture_dir.glob("*_opacity_color.tga"))
    require(all(len(files) == 1 for files in textures.values()),
            "original verified body/head color and normal textures missing")
    require(len(opacity_files) <= 1, "ambiguous opacity image")
    if opacity_files:
        textures["opacity_color"] = opacity_files
    images = {
        role: bpy.data.images.load(str(files[0]), check_existing=True)
        for role, files in textures.items()
    }
    assigned = []
    # Factory-startup keeps unused materials such as 'Material' and
    # 'Dots Stroke' in bpy.data; audit only materials referenced by the
    # verified imported human mesh, not unused Blender factory datablocks.
    used_materials = {
        m for obj in bpy.context.scene.objects if obj.type == "MESH"
        for m in obj.data.materials if m is not None
    }
    for mat in sorted(used_materials, key=lambda m: m.name):
        name = mat.name.lower()
        role = ("head" if "head" in name else
                "body" if "body" in name else
                "opacity" if "opacity" in name else None)
        if role is None:
            raise ValueError("unrecognized used FBX material: " + mat.name)
        require(role != "opacity" or "opacity_color" in images,
                "hair/eyelash opacity texture required for this female mesh")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()  # no unresolved source image paths in final package
        out = nodes.new("ShaderNodeOutputMaterial")
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        bsdf.inputs["Roughness"].default_value = .82 if role != "opacity" else .75
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = images["opacity_color" if role == "opacity" else role+"_color"]
        tex.label = f"Rocketbox verified {role} texture"
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        if role == "opacity":
            mat.node_tree.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
            if hasattr(mat, "surface_render_method"):
                mat.surface_render_method = "DITHERED"
        else:
            normal_img = images[role+"_normal"]
            normal_img.colorspace_settings.name = "Non-Color"
            normal_tex = nodes.new("ShaderNodeTexImage")
            normal_tex.image = normal_img
            nmap = nodes.new("ShaderNodeNormalMap")
            nmap.inputs["Strength"].default_value = .5
            mat.node_tree.links.new(normal_tex.outputs["Color"], nmap.inputs["Color"])
            mat.node_tree.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        assigned.append({"name": mat.name, "status": role.upper() + "_TEXTURED"})
    for role, image in images.items():
        require(image.has_data and min(image.size) >= 1024,
                "source texture not decoded: " + role)
    return assigned


def bounds(meshes):
    mini = Vector((float("inf"),) * 3)
    maxi = Vector((-float("inf"),) * 3)
    for o in meshes:
        for corner in o.bound_box:
            p = o.matrix_world @ Vector(corner)
            for i in range(3):
                mini[i] = min(mini[i], p[i])
                maxi[i] = max(maxi[i], p[i])
    return mini, maxi


def screenshot(output, meshes):
    mini, maxi = bounds(meshes)
    center = (mini + maxi) / 2
    height = maxi.z - mini.z
    require(math.isfinite(height) and height > .01,
            "avatar geometry degenerate")
    bpy.ops.object.camera_add(location=center + Vector(
        (height * .65, -height * 2.8, height * .12)
    ))
    cam = bpy.context.object
    cam.name = "Diagnostic studio camera (excluded)"
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = height * 1.55
    bpy.context.scene.camera = cam
    for name, pos, energy in (
        ("Key", center + Vector((height, -height, height)), 750),
        ("Fill", center + Vector((-height, height * .6, height)), 350),
    ):
        bpy.ops.object.light_add(type="AREA", location=pos)
        lamp = bpy.context.object
        lamp.name = f"Diagnostic {name} (excluded)"
        lamp.data.energy = energy
        lamp.data.size = height
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 12
    scene.render.resolution_x = 512
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (.11, .12, .14)
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    return [round(v, 5) for v in (*mini, *maxi)]


def generate(source: Path, out: Path):
    provenance = json.loads((source / "source_provenance.json").read_text(
        encoding="utf-8"
    ))
    require(provenance["license_spdx"] == "MIT"
            and (source / "UPSTREAM_LICENSE.md").is_file(),
            "source copyright notice missing")
    path = source / provenance["files"]["fbx"]["relative_path"]
    require(path.is_file() and sha(path) == provenance["files"]["fbx"]["sha256"],
            "FBX differs from authenticated upstream")
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    # Blender 5+ ships the new C++ FBX importer. The legacy Python operator
    # is broken on the Ubuntu Blender 5.0.1 package ('ImportFBX.files'
    # missing) and is deprecated by Blender's official pipeline notes.
    if bpy.app.version >= (5, 0, 0):
        bpy.ops.wm.fbx_import(filepath=str(path))
    else:
        bpy.ops.import_scene.fbx(filepath=str(path))
    rigs = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    print("EMS_ROCKETBOX_IMPORT_DETAILS=" + json.dumps({
        "rigs": [r.name for r in rigs],
        "meshes": [{"name": m.name, "verts": len(m.data.vertices),
                    "materials": [x.name for x in m.data.materials]} for m in meshes],
        "bones": {r.name: [b.name for b in r.data.bones] for r in rigs},
    }))
    require(rigs and meshes, "upstream FBX is not a rigged human mesh")
    valid_skin = [m for m in meshes if any(
        mod.type == "ARMATURE" and mod.object in rigs for mod in m.modifiers
    ) and sum(bool(v.groups) for v in m.data.vertices) > 100]
    require(valid_skin, "upstream avatar missing weighted deformable skin")
    require(max(len(x.data.bones) for x in rigs) >= 25,
            "upstream humanoid contains fewer than 25 bones")
    materials = attach_color_materials(source)
    minmax = bounds(valid_skin)
    height_m = minmax[1].z - minmax[0].z
    # Do not pretend uncalibrated FBX units are meters. Keep all original
    # transforms and state the observed bounds in report.
    editable = out / "source.blend"
    glb = out / "avatar.glb"
    preview = out / "rest_review.png"
    screenshot(preview, valid_skin)
    bpy.ops.wm.save_as_mainfile(filepath=str(editable))
    bpy.ops.object.select_all(action="DESELECT")
    for rig in rigs:
        rig.select_set(True)
    for mesh in meshes:
        mesh.select_set(True)
    bpy.context.view_layer.objects.active = rigs[0]
    bpy.ops.export_scene.gltf(
        filepath=str(glb), export_format="GLB",
        use_selection=True, export_skins=True,
        export_animations=False, export_cameras=False, export_lights=False,
    )
    require(all(x.stat().st_size > 1024 for x in
                (editable, glb, preview)), "real avatar export missing")
    data = {
        "source": "microsoft/Microsoft-Rocketbox",
        "source_commit": provenance["upstream_commit"],
        "source_avatar": provenance["avatar"],
        "variant": provenance["variant"],
        "license": "MIT",
        "license_notice": "UPSTREAM_LICENSE.md",
        "body_height_as_imported": round(float(height_m), 6),
        "armature_count": len(rigs),
        "bone_count_by_rig": {r.name: len(r.data.bones) for r in rigs},
        "skinned_mesh_count": len(valid_skin),
        "weighted_vertices_by_mesh": {
            m.name: sum(bool(v.groups) for v in m.data.vertices) for m in valid_skin},
        "material_bindings": materials,
        "actual_source_bounds_xyz": [list(map(float, bound)) for bound in minmax],
        "editable_blend_sha256": sha(editable),
        "exported_glb_sha256": sha(glb),
        "preview_png_sha256": sha(preview),
        "retarget_video_qa": "NOT_TESTED",
        "human_visual_approval": "PENDING",
        "commercial_asset_approval": False,
    }
    # AssetCatalog schema: imported third-party skinned human with original
    # MIT provenance, no invented rigidbody/IK or distribution signoff.
    low, high = minmax
    avatar_id = f"ems.avatar.rocketbox.sports.{provenance['variant']}.01"
    manifest = {
        "schema_version": "1.0",
        "asset_id": avatar_id,
        "version": "0.1.0",
        "category": "human_avatar",
        "subcategory": "sports_adult",
        "variant": provenance["variant"],
        "unit": "meter",
        "dimensions_m": {
            "length_x": round(high.x - low.x, 6),
            "width_y": round(high.y - low.y, 6),
            "height_z": round(high.z - low.z, 6),
        },
        "coordinate_system": "Blender Z-up meters (glTF normalized Y-up)",
        "rig": {
            "profile_id": "ems.humanoid.rocketbox.sports.v1",
            "bones": len(rigs[0].data.bones),
            "skin_weights": "PRESENT_NOT_RETARGET_VALIDATED",
            "deformation_review": "PENDING_GLTF_QA",
        },
        "grip_points": [],
        "attachment_points": [
            {
                "id": ident,
                "position_m": [round(float(v), 6) for v in
                               (rigs[0].matrix_world @ rigs[0].pose.bones[bone].head)]
            }
            for ident, bone in (
                ("left_wrist", "Bip01 L Hand"),
                ("right_wrist", "Bip01 R Hand"),
                ("left_ankle", "Bip01 L Foot"),
                ("right_ankle", "Bip01 R Foot"),
            )
        ],
        "contact_surfaces": [],
        "collision_shapes": [],
        "kinematics": {"type": "deformable_humanoid",
                       "retarget_qa": "NOT_TESTED",
                       "ik": "NOT_IMPLEMENTED"},
        "models": {"editable": "source.blend",
                   "distribution": "avatar.glb",
                   "thumbnail": "rest_review.png"},
        "source": {
            "kind": "VERIFIED_THIRD_PARTY",
            "upstream_repository": provenance["upstream_repository"],
            "upstream_commit": provenance["upstream_commit"],
            "source_file": provenance["files"]["fbx"]["relative_path"],
            "source_sha256": provenance["files"]["fbx"]["sha256"],
            "license_notice": "UPSTREAM_LICENSE.md",
        },
        "licenses": {
            "spdx": "MIT",
            "original_notice": "UPSTREAM_LICENSE.md",
            "source_permission": "COMMERCIAL_USE_AND_REDISTRIBUTION_WITH_NOTICE",
            "status": "PENDING",
            "distribution_approved": False,
            "reviewer": None,
        },
        "qa": {"roundtrip": "NOT_TESTED",
               "human_visual_review": "PENDING",
               "commercial_approval": False},
        "file_sha256": {
            "source.blend": data["editable_blend_sha256"],
            "avatar.glb": data["exported_glb_sha256"],
            "rest_review.png": data["preview_png_sha256"],
        },
    }
    (out / "asset.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False)+"\n",
        encoding="utf-8",
    )
    (out / "import_report.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("EMS_ROCKETBOX_IMPORTED=" + json.dumps({
        "variant": data["variant"], "rigs": data["armature_count"],
        "bones": data["bone_count_by_rig"],
        "skinned_meshes": data["skinned_mesh_count"],
        "body_height_as_imported": data["body_height_as_imported"],
        "commercial_asset_approval": False,
    }))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--source-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args(argv)
    generate(args.source_dir.resolve(strict=True), args.output_dir.resolve())
