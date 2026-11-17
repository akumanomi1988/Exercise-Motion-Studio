"""Exercise Motion Studio bootstrap CLI. No YouTube downloader."""

import argparse
import json
import sys

from ems import __version__
from ems.doctor import inspect_environment
from ems.jobs import register_source
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
        else:
            raise InputValidationError("unsupported command")
    except (InputValidationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
