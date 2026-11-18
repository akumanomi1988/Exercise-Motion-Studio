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
    """Explicitly reference supplied upstream images, not generated material."""
    textures = {name: sorted((source / "Textures").glob("*_" + name + ".tga"))
                for name in ("body_color", "head_color",
                             "body_normal", "head_normal")}
    require(all(len(files) == 1 for files in textures.values()),
            "pinned body/head color and normal textures unavailable")
    images = {role: bpy.data.images.load(str(files[0]), check_existing=True)
              for role, files in textures.items()}
    assigned = []
    materials = sorted(bpy.data.materials, key=lambda m: m.name)
    for mat in materials:
        name = mat.name.lower()
        # Important: don't claim textures assigned when FBX material names
        # are unrecognized. Classification is audited in output JSON.
        role = ("head" if any(x in name for x in ("head", "face", "skinhead"))
                else "body" if any(x in name for x in ("body", "torso", "cloth"))
                else None)
        if role is None:
            assigned.append({"name": mat.name, "status": "UNMAPPED"})
            continue
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is None:
            assigned.append({"name": mat.name, "status": "NO_PRINCIPLED"})
            continue
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = images[f"{role}_color"]
        tex.label = "Microsoft Rocketbox " + role + " color"
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        normal_img = images[f"{role}_normal"]
        normal_img.colorspace_settings.name = "Non-Color"
        normal_tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        normal_tex.image = normal_img
        nmap = mat.node_tree.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value = .5
        mat.node_tree.links.new(normal_tex.outputs["Color"], nmap.inputs["Color"])
        mat.node_tree.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        assigned.append({"name": mat.name, "status": role.upper() + "_TEXTURED"})
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
    bpy.ops.import_scene.fbx(filepath=str(path), use_image_search=True)
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
        "actual_source_bounds_xyz": minmax,
        "editable_blend_sha256": sha(editable),
        "exported_glb_sha256": sha(glb),
        "preview_png_sha256": sha(preview),
        "retarget_video_qa": "NOT_TESTED",
        "human_visual_approval": "PENDING",
        "commercial_asset_approval": False,
    }
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
