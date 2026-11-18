"""Download two pinned, genuine Microsoft Rocketbox sports avatars (MIT).

Authoritative source: microsoft/Microsoft-Rocketbox at a pinned upstream commit.
Fetches actual FBX meshes, PBR color/normal textures, reference PNG and LICENSE.
Fails closed on Git blob SHA-1 mismatch, HTTP errors or excessively large files.
No third-party model weights, videos, cloud account or Docker required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

UPSTREAM = "microsoft/Microsoft-Rocketbox"
COMMIT = "0943055db6ec570bcef9f2c8b41c9e5467c808f9"
BASE = f"https://raw.githubusercontent.com/{UPSTREAM}/{COMMIT}/"
FILE_SPECS = {
    "male": {
        "name": "Sports_Male_01",
        "fbx": ("Export/Sports_Male_01.fbx",
                "e06668c448908b434f1032cf5922953aa9c58393"),
        "reference": ("Sports_Male_01.png",
                      "1c7dff80155bfa3a0b4445ef21ac4680bf828dc5"),
        "body_color": ("Textures/m021_body_color.tga",
                       "fc031787b8c19d93ff8e06bc814456f5646e7c85"),
        "head_color": ("Textures/m021_head_color.tga",
                       "67d497afd907ff3a5dceded82dbed8bef5c8636e"),
        "body_normal": ("Textures/m021_body_normal.tga",
                        "68433f2e188f57e1a0ba4d4b9d1b44ab922580b3"),
        "head_normal": ("Textures/m021_head_normal.tga",
                        "55c197f2e060eca983d34ee7e43f81f81ccf2898"),
    },
    "female": {
        "name": "Sports_Female_01",
        "fbx": ("Export/Sports_Female_01.fbx",
                "d020af6fde28ba7a9f5077f4cbe7f3b2414c49a9"),
        "reference": ("Sports_Female_01.png",
                      "3194a26e5670ca1cfd3020ef8d3122e49c8169d0"),
        "body_color": ("Textures/f021_body_color.tga",
                       "e22068125d9d35388f48ccbc493af021c55fecd0"),
        "head_color": ("Textures/f021_head_color.tga",
                       "cb4258da46d21ef5ae2b3017cefba6b5bf5d3acc"),
        "body_normal": ("Textures/f021_body_normal.tga",
                        "8c65fe177ce466e2847db870f879e8a2fc409b1"),
        "head_normal": ("Textures/f021_head_normal.tga",
                        "804553aad3323cdd88e54fab62bbc3a25b4f20bc"),
    },
}
LICENSE_BLOB_SHA1 = "9bcfb3ece5301a55d3a41bbd00a029ab27d61d13"


def git_blob_sha1(data: bytes) -> str:
    """Git hash-object: SHA1('blob <size>\0' + bytes), NOT raw-file SHA1."""
    return hashlib.sha1(
        b"blob " + str(len(data)).encode() + b"\0" + data
    ).hexdigest()


def download(url: str, output: Path, expected_blob_sha: str) -> dict:
    if output.is_file() and git_blob_sha1(output.read_bytes()) == expected_blob_sha:
        data = output.read_bytes()
    else:
        request = Request(url, headers={"User-Agent": "Exercise-Motion-Studio/0.1"})
        with urlopen(request, timeout=90) as response:
            if response.status != 200:
                raise RuntimeError(f"asset fetch failed: HTTP {response.status}")
            data = response.read(32 * 1024 * 1024 + 1)
        if len(data) > 32 * 1024 * 1024:
            raise ValueError("upstream file exceeds per-file limit")
        if git_blob_sha1(data) != expected_blob_sha:
            raise ValueError(f"upstream Git SHA mismatch: {url}; "
                             f"expected={expected_blob_sha} actual={git_blob_sha1(data)} "
                             f"bytes={len(data)} preview={data[:48]!r}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
    return {
        "source_url": url,
        "source_git_blob_sha1": expected_blob_sha,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "local_file": output.name,
    }


def acquire(root: Path, variants: tuple[str, ...]) -> None:
    for variant in variants:
        specification = FILE_SPECS[variant]
        ident = specification["name"]
        folder = root / variant
        folder.mkdir(parents=True, exist_ok=True)
        files = {}
        for role in ("fbx", "reference", "body_color", "head_color",
                     "body_normal", "head_normal"):
            rel, blobsha = specification[role]
            url = BASE + f"Assets/Avatars/Professions/{ident}/" + rel
            path = folder / rel
            files[role] = download(url, path, blobsha)
            files[role]["relative_path"] = rel
        license_info = download(BASE + "LICENSE.md", folder / "UPSTREAM_LICENSE.md",
                                LICENSE_BLOB_SHA1)
        if b"Permission is hereby granted" not in (folder / "UPSTREAM_LICENSE.md").read_bytes():
            raise ValueError("MIT permission notice absent from pinned source")
        meta = {
            "schema_version": "1.0",
            "upstream_repository": f"https://github.com/{UPSTREAM}",
            "upstream_commit": COMMIT,
            "avatar": ident,
            "variant": variant,
            "license_spdx": "MIT",
            "license_text": "UPSTREAM_LICENSE.md",
            "license_file": license_info,
            "commercial_permission_from_upstream": True,
            "commercial_release_approved_for_ems": False,
            "technical_qa": "NOT_TESTED",
            "files": files,
        }
        (folder / "source_provenance.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print("EMS_UPSTREAM_AVATAR=" + json.dumps({
            "variant": variant, "avatar": ident,
            "upstream_commit": COMMIT,
            "files": len(files), "rights": "MIT_UPSTREAM; EMS_QA_PENDING",
        }))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--variant", choices=("male", "female", "both"),
                        default="both")
    args = parser.parse_args()
    variants = ("male", "female") if args.variant == "both" else (args.variant,)
    acquire(args.output_dir.expanduser().resolve(), variants)
