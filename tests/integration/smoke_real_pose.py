"""An actual human exercise clip and actual MediaPipe inference, not a mock.

Input clip must have independent documentation of processing rights. This test
is NOT an approval of biomechanical reconstruction, commercial derivative
distribution, retargeting or animation.
"""

import argparse
import json
import math
import shutil
import tempfile
from pathlib import Path

from ems.jobs import register_source
from ems.media import probe_registered_video
from ems.pose import capture_registered_video
from ems.solver import solve_registered_capture


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--video", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--model-sha256", required=True)
    p.add_argument("--qa-output", type=Path, help="Optional local diagnostic pose output")
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
        # Run actual geometric constraint solver on the exact capture artifacts.
        # This remains an intermediate with no calibrated root or avatar.
        solution = solve_registered_capture(job["job_id"], jobs_dir=jobs)
        solved = json.loads(
            (jobs / job["job_id"] / "solved_skeleton.json").read_text(encoding="utf-8")
        )
        assert solution["status"] == "INTERMEDIATE_SKELETON_REVIEW_REQUIRED"
        assert len(solved["frames"]) == len(pose["frames"])
        assert solved["qa"]["length_1_percent_check"] == "TECHNICAL_PASS"
        assert solved["qa"]["max_solved_relative_segment_length_deviation"] <= 0.01
        assert solved["qa"]["commercial_approval"] is False
        assert solved["qa"]["absolute_root_motion"] == "NOT_SOLVED"
        assert solved["data_type"] == "INTERMEDIATE_SKELETON_NOT_FINAL_MOTION"
        if args.qa_output is not None:
            folder = args.qa_output.resolve()
            folder.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(
                jobs / job["job_id"] / "pose_raw.json", folder / "pose_raw.json"
            )
            shutil.copyfile(
                jobs / job["job_id"] / "solved_skeleton.json",
                folder / "solved_skeleton.json"
            )
            (folder / "SOURCE_ATTRIBUTION.txt").write_text(
                "Diagnostic source: Basic single leg squat.webm by RickyBennison\n"
                "Source: https://commons.wikimedia.org/wiki/File:Basic_single_leg_squat.webm\n"
                "License: Creative Commons Attribution-ShareAlike 4.0 International\n"
                "https://creativecommons.org/licenses/by-sa/4.0/\n"
                "Changes: sampled and transformed to raw MediaPipe landmarks; "
                "later rendered as a diagnostic skeletal visualization.\n"
                "Adaptations (captured motion, constrained skeleton and associated "
                "GLB/PNG/WebP previews) are shared under CC BY-SA 4.0 to the "
                "extent derived from this licensed source.\n"
                "NOT commercially approved. No original video copied into the output.\n",
                encoding="utf-8",
            )
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
            "solved_skeleton_sha256": solution["sha256"],
            "solved_segment_max_relative_error": solved["qa"]["max_solved_relative_segment_length_deviation"],
            "raw_segment_max_relative_error": solved["qa"]["max_raw_relative_segment_length_deviation"],
            "solved_length_qa_only": solved["qa"]["length_1_percent_check"],
            "review_required": True,
            "retarget_done": False,
            "visual_qa_done": False,
            "g1_pass": False,
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
