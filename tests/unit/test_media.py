"""Integration boundary tests: actual FFmpeg-encoded frames, not exercise MoCap.

A generated test-pattern clip validates only container/codec decoding.
It must NEVER count toward T01-T10 or a G1 capture/visual-quality PASS.
"""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from ems.jobs import register_source
from ems.media import probe_registered_video
from ems.rights import InputValidationError


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and FFprobe required for media integration tests")
class MediaProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.source = root / "video.mp4"
        self.jobs_dir = root / "jobs"
        subprocess.run(
            ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
             "-f", "lavfi", "-i", "testsrc2=size=64x48:rate=12",
             "-t", "0.5", "-an", "-c:v", "mpeg4", "-y", str(self.source)],
            check=True, capture_output=True, timeout=20,
        )

    def register(self):
        return register_source(
            source=self.source, exercise_id="T01", rights_basis="owned",
            rights_evidence="CI-generated test pattern; not a human exercise",
            jobs_dir=self.jobs_dir,
        )

    def test_full_decode_preserves_unapproved_rights_and_capture_state(self):
        job = self.register()
        result = probe_registered_video(job["job_id"], self.jobs_dir)
        self.assertEqual(result["status"], "VIDEO_PROBED")
        self.assertEqual(result["media_probe"]["validation"], "FULL_STREAM_DECODED")
        self.assertEqual(result["media_probe"]["codec"], "mpeg4")
        self.assertEqual(result["media_probe"]["width"], 64)
        self.assertEqual(result["media_probe"]["height"], 48)
        self.assertGreater(result["media_probe"]["decoded_frames"], 0)
        self.assertGreater(result["media_probe"]["duration_seconds"], 0)
        self.assertAlmostEqual(result["media_probe"]["average_fps"], 12, places=1)
        self.assertEqual(result["capture"], "NOT_STARTED")
        self.assertFalse(result["commercial_approval"])
        persisted = json.loads(
            (self.jobs_dir / job["job_id"] / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(persisted["pipeline"]["probe"], "PASS")
        self.assertEqual(persisted["pipeline"]["capture"], "NOT_STARTED")
        self.assertEqual(persisted["rights"]["status"], "USER_ATTESTED")
        self.assertFalse(persisted["rights"]["commercial_approval"])

    def test_refuses_mutated_source_and_preserves_manifest(self):
        job = self.register()
        self.source.write_bytes(b"tampered-media")
        with self.assertRaisesRegex(InputValidationError, "changed since"):
            probe_registered_video(job["job_id"], self.jobs_dir)
        persisted = json.loads(
            (self.jobs_dir / job["job_id"] / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("media_probe", persisted)

    def test_refuses_fake_mp4_registered_by_legacy_cli(self):
        self.source.write_bytes(b"not a video")
        job = self.register()
        with self.assertRaises(InputValidationError):
            probe_registered_video(job["job_id"], self.jobs_dir)
        persisted = json.loads(
            (self.jobs_dir / job["job_id"] / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(persisted["pipeline"]["capture"], "NOT_STARTED")
        self.assertNotIn("media_probe", persisted)

    def test_refuses_unsafe_job_identifier(self):
        with self.assertRaises(InputValidationError):
            probe_registered_video("../escape", self.jobs_dir)

    def test_requires_valid_decode_timeout(self):
        job = self.register()
        with self.assertRaises(InputValidationError):
            probe_registered_video(job["job_id"], self.jobs_dir, decode_timeout_s=0)

    def test_probe_is_repeatable_without_enabling_commercial_export(self):
        job = self.register()
        first = probe_registered_video(job["job_id"], self.jobs_dir)
        second = probe_registered_video(job["job_id"], self.jobs_dir)
        self.assertEqual(first["media_probe"]["source_sha256"],
                         second["media_probe"]["source_sha256"])
        self.assertFalse(second["commercial_approval"])
