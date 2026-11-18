"""Encode REAL Blender-rendered skinned-human review frames into animated WebP.

No synthesized source motion, source footage, or third-party model is packaged.
Outputs remain license/biomechanics/visual REVIEW_REQUIRED, not publishable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

p = argparse.ArgumentParser()
p.add_argument("--output-dir", type=Path, required=True)
args = p.parse_args()
root = args.output_dir.resolve(strict=True)
manifest_file = root / "retarget_manifest.json"
meta = json.loads(manifest_file.read_text(encoding="utf-8"))
assert meta["data_type"] == "SKINNED_HUMAN_RETARGET_DIAGNOSTIC_NOT_FINAL_MOTION"
assert meta["commercial_approval"] is False
frames = sorted((root / "frames").glob("frame_*.png"))
assert len(frames) == 8, "eight genuine Blender review frames required"
images = []
for path in frames:
    with Image.open(path) as img:
        assert img.size == (512, 768), f"wrong frame dimensions: {path}"
        images.append(img.convert("RGB"))
assert any(ImageChops.difference(images[0], img).getbbox() is not None
           for img in images[1:]), "all rendered human frames look identical"
output = root / "retarget_review.webp"
images[0].save(output, "WEBP", save_all=True,
               append_images=images[1:], duration=180,
               loop=0, quality=80, method=4)
with Image.open(output) as verify:
    assert getattr(verify, "n_frames", 1) >= 2, "not an animated WebP"
meta["outputs"]["webp"] = "retarget_review.webp"
meta["file_sha256"]["retarget_review.webp"] = hashlib.sha256(
    output.read_bytes()
).hexdigest()
meta["webp_frames"] = len(images)
manifest_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
print("EMS_REAL_HUMAN_WEBP=" + json.dumps({
    "variant": meta["variant"], "frames": len(images),
    "webp_bytes": output.stat().st_size,
    "animated": True, "commercial_approval": False,
}))
