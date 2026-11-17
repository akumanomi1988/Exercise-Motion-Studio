"""Tests are for registration only, not video decoding or motion fidelity."""

import json
import tempfile
import unittest
from pathlib import Path

from ems.jobs import register_source
from ems.rights import InputValidationError


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # Deliberately NOT a decodable video: tests the registration boundary only.
        self.source = self.root / "synthetic.mp4"
        self.source.write_bytes(b"fake-video-bytes-for-registration-tests-only")
        self.jobs_dir = self.root / "jobs"

    def register(self, **changes):
        args = {
            "source": self.source,
            "exercise_id": "T01",
            "rights_basis": "owned",
            "rights_evidence": "Internal test fixture (not a real exercise clip)",
            "jobs_dir": self.jobs_dir,
        }
        args.update(changes)
        return register_source(**args)

    def test_registration_creates_attested_not_approved_manifest(self):
        job = self.register()
        self.assertEqual(job["status"], "REGISTERED")
        self.assertEqual(job["rights"]["status"], "USER_ATTESTED")
        self.assertFalse(job["rights"]["commercial_approval"])
        self.assertEqual(job["pipeline"]["capture"], "NOT_STARTED")
        path = self.jobs_dir / job["job_id"] / "manifest.json"
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), job)

    def test_idempotent_same_file_same_rights(self):
        first = self.register()
        second = self.register()
        self.assertEqual(first, second)
        self.assertEqual(len(list(self.jobs_dir.iterdir())), 1)

    def test_modified_content_creates_distinct_job(self):
        first = self.register()
        self.source.write_bytes(b"modified-test-bytes")
        self.assertNotEqual(first["job_id"], self.register()["job_id"])

    def test_requires_rights_evidence(self):
        with self.assertRaises(InputValidationError):
            self.register(rights_evidence="  ")

    def test_rejects_unsupported_license(self):
        with self.assertRaises(InputValidationError):
            self.register(rights_basis="research-only")

    def test_rejects_unsafe_exercise_id(self):
        with self.assertRaises(InputValidationError):
            self.register(exercise_id="../../escape")

    def test_rejects_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            self.register(source=self.root / "missing.mp4")

    def test_rejects_unknown_extension(self):
        other = self.root / "unsafe.py"
        other.write_text("print('not video')", encoding="utf-8")
        with self.assertRaises(InputValidationError):
            self.register(source=other)


if __name__ == "__main__":
    unittest.main()
