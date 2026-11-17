"""Read-only environment diagnostics; not an end-to-end acceptance gate."""

import platform
import shutil
import sys


def inspect_environment() -> dict:
    dependencies = {
        name: shutil.which(name)
        for name in ("ffmpeg", "ffprobe", "blender", "dotnet", "git")
    }
    python_ok = sys.version_info >= (3, 11)
    return {
        "python_version": platform.python_version(),
        "python_supported": python_ok,
        "os": platform.platform(),
        "windows_target": sys.platform == "win32",
        "executables": dependencies,
        "capture_ready_candidate": bool(
            python_ok and dependencies["ffmpeg"] and dependencies["ffprobe"]
            and dependencies["blender"]
        ),
        "commercial_approval": False,
        "message": "Diagnostic only: no video capture, retarget, render or license QA performed.",
    }
