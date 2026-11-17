"""An actual human exercise clip and actual MediaPipe inference, not a mock.

Input clip must have independent documentation of processing rights. This test
is NOT an approval of biomechanical reconstruction, commercial derivative
distribution, retargeting or animation.
"""

import argparse
import json
import math
import tempfile
from pathlib import Path

from ems.jobs import register_source
from ems.media import probe_registered_video
from ems.pose import capture_registered_video


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--video", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--model-sha256", required=True)
    args = p.parse_args()

    with tempfile.TemporaryDirectory(prefix="ems-real-human-smoke-") as directory:
        jobs = Path(directory) / "jobs"
        job = register_source(
            source=args.video,
            exercise_id="T01_OBSERVATION_ONLY",
            rights_basis="licensed",
            rights_evidence=(
                "RickyBennison own work; CC BY-SA 4.0: "
                "https://commons.wikimedia.org/wiki/File:Basic_single_leg_squat.webm ; "
                "https://creativecommons.org/licenses/by-sa/4.0/"
            ),
            jobs_dir=jobs,
        )
        probe = probe_registered_video(job["job_id"], jobs, decode_timeout_s=90)
        assert probe["media_probe"]["decoded_frames"] > 0
        result = capture_registered_video(
            job_id=job["job_id"], model_path=args.model,
            model_sha256=args.model_sha256, jobs_dir=jobs, sample_fps=6,
            resolution=512, max_duration_s=30,
        )
        pose = json.loads(
            (jobs / job["job_id"] / "pose_raw.json").read_text(encoding="utf-8")
        )
        frames = [x for x in pose["frames"] if x["state"] == "DETECTED"]
        assert len(frames) >= 5, (
            "MediaPipe did not find a human pose on enough real frames"
        )
        times = [x["timestamp_ms"] for x in pose["frames"]]
        assert all(b > a for a, b in zip(times, times[1:]))
        assert all(len(x["world_landmarks"]) == 33 for x in frames)
        # Verify observations vary, using genuine hip-relative ankle trajectories.
        # This only proves non-static output, NOT biomechanical fidelity.
        left_ankle = [f["world_landmarks"][27] for f in frames]
        span = max(j["y"] for j in left_ankle) - min(j["y"] for j in left_ankle)
        assert math.isfinite(span) and span > 0.005, (
            f"raw landmarks look static; ankle vertical span={span}"
        )
        assert result["status"] == "CAPTURED_REVIEW_REQUIRED"
        assert pose["qa"]["commercial_approval"] is False
        assert pose["space"]["absolute_root_motion"] is False
        assert pose["qa"]["gate_g1"] == "NOT_EVALUATED"
        manifest = json.loads(
            (jobs / job["job_id"] / "manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["pipeline"]["capture"] == "REVIEW_REQUIRED"
        assert manifest["rights"]["status"] == "USER_ATTESTED"
        print("REAL_VIDEO_POSE_SMOKE_PASS=" + json.dumps({
            "human_reference": "RickyBennison / Wikimedia Commons / CC BY-SA 4.0",
            "input_sha256": job["source"]["sha256"],
            "model_sha256": pose["model"]["sha256"],
            "frames_total": len(pose["frames"]),
            "frames_detected": len(frames),
            "coverage": pose["qa"]["detection_coverage"],
            "mean_core_visibility": pose["qa"]["mean_core_visibility"],
            "ankle_relative_y_span_m": round(span, 6),
            "pose_sha256": result["sha256"],
            "review_required": True,
            "retarget_done": False,
            "visual_qa_done": False,
            "g1_pass": False,
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
