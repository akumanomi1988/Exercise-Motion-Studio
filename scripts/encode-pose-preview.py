"""Encode diagnostic Blender PNG frames as animated WebP using Pillow.

No sourced image or real video is embedded. Source license and attribution
remain in SOURCE_ATTRIBUTION.txt. No commercial approval follows from encoding.
"""
import argparse
import json
from pathlib import Path
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("--asset-dir", type=Path, required=True)
args = parser.parse_args()
root = args.asset_dir.resolve(strict=True)
files = sorted((root / "frames").glob("frame_*.png"))
assert len(files) >= 2, "at least two genuinely rendered frames required"
frames = [Image.open(path).convert("RGB") for path in files]
output = root / "pose_debug.webp"
frames[0].save(
    output, format="WEBP", save_all=True,
    append_images=frames[1:], duration=180, loop=0,
    quality=80, method=4,
)
with Image.open(output) as verify:
    assert getattr(verify, "n_frames", 1) >= 2, "WebP lacks animation"
manifest = json.loads((root / "debug_manifest.json").read_text(encoding="utf-8"))
manifest["animation_webp"] = output.name
manifest["webp_frames"] = len(frames)
(root / "debug_manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
)
print("EMS_DEBUG_WEBP_QA=" + json.dumps({
    "file": str(output), "frames": len(frames), "bytes": output.stat().st_size,
    "human_visual_approval": False, "commercial_approval": False,
}))
