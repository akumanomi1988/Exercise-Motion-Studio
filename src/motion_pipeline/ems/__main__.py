"""Exercise Motion Studio bootstrap CLI. No YouTube downloader."""

import argparse
import json
import sys

from ems import __version__
from ems.catalog import inspect_asset_folder
from ems.doctor import inspect_environment
from ems.jobs import register_source
from ems.media import probe_registered_video
from ems.rights import ALLOWED_RIGHTS_BASES, InputValidationError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ems", description="Exercise Motion Studio control plane (pre-MoCap)"
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Inspect local FFmpeg/Blender/.NET prerequisites")
    register = sub.add_parser(
        "register", help="Register a local source with a rights declaration; no inference"
    )
    register.add_argument("--source", required=True, help="Local MP4/MOV/WebM file")
    register.add_argument("--exercise-id", required=True)
    register.add_argument("--rights-basis", choices=sorted(ALLOWED_RIGHTS_BASES), required=True)
    register.add_argument("--rights-evidence", required=True)
    register.add_argument("--jobs-dir", default="data/jobs")
    probe = sub.add_parser(
        "probe", help="Verify a registered video's metadata and decode all frames"
    )
    probe.add_argument("--job-id", required=True, help="24-character registration identifier")
    probe.add_argument("--jobs-dir", default="data/jobs")
    probe.add_argument("--decode-timeout-s", type=int, default=300)
    asset = sub.add_parser("asset-check", help="Verify asset.json integrity only; not geometry QA")
    asset.add_argument("--asset-dir", required=True)
    asset.add_argument("--require-commercial", action="store_true",
                       help="Block unless distribution rights review is recorded")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            result = inspect_environment()
        elif args.command == "register":
            result = register_source(
                source=args.source,
                exercise_id=args.exercise_id,
                rights_basis=args.rights_basis,
                rights_evidence=args.rights_evidence,
                jobs_dir=args.jobs_dir,
            )
        elif args.command == "probe":
            result = probe_registered_video(
                job_id=args.job_id,
                jobs_dir=args.jobs_dir,
                decode_timeout_s=args.decode_timeout_s,
            )
        elif args.command == "asset-check":
            result = inspect_asset_folder(
                args.asset_dir, require_commercial=args.require_commercial
            )
        else:
            raise InputValidationError("unsupported command")
    except (InputValidationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
