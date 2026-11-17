"""AG1 cross-avatar compatibility metadata check (after Blender GLB round-trip).

Human visual quality and motion retarget are separate acceptance requirements.
"""
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--root", type=Path, required=True)
args = p.parse_args()
root = args.root.resolve(strict=True)
male = json.loads((root / "male" / "asset.json").read_text(encoding="utf-8"))
female = json.loads((root / "female" / "asset.json").read_text(encoding="utf-8"))
mqa = json.loads((root / "male" / "qa_report.json").read_text(encoding="utf-8"))
fqa = json.loads((root / "female" / "qa_report.json").read_text(encoding="utf-8"))
assert male["variant"] == "male"
assert female["variant"] == "female"
assert male["rig"]["profile_id"] == female["rig"]["profile_id"]
assert male["rig"]["bones"] == female["rig"]["bones"], (
    "Male and female must share identical named hierarchy for retarget mapping"
)
assert male["rig"]["base_vertex_count"] == female["rig"]["base_vertex_count"], (
    "MakeHuman CC0 base must have compatible topology for shared tests"
)
assert male["rig"]["evaluated_mesh_sha256"] != female["rig"]["evaluated_mesh_sha256"], (
    "Male and female meshes are identical; gender morphing did not apply"
)
for meta, qa in ((male, mqa), (female, fqa)):
    assert qa["technical_rig_roundtrip"] == "PASS"
    assert qa["deformation_max_distance_m"] > 0.002
    assert meta["licenses"]["status"] == "PENDING"
    assert meta["licenses"]["distribution_approved"] is False
    assert meta["rig"]["animation"] == "NOT_PRESENT"
result = {
    "status": "DUAL_AVATAR_TECHNICAL_RIG_PASS",
    "shared_profile": male["rig"]["profile_id"],
    "shared_named_bones": len(male["rig"]["bones"]),
    "shared_topology_vertices": male["rig"]["base_vertex_count"],
    "male_morph_digest": male["rig"]["evaluated_mesh_sha256"],
    "female_morph_digest": female["rig"]["evaluated_mesh_sha256"],
    "both_skin_deform_test_passed": True,
    "human_visual_review": "PENDING",
    "pose_retarget": "NOT_TESTED",
    "commercial_approval": False,
    "ag1_pass": False,
}
(root / "dual_avatar_qa.json").write_text(json.dumps(result, indent=2) + "\n")
print("EMS_DUAL_AVATAR_QA=" + json.dumps(result))
