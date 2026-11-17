import io
import json
import unittest
from contextlib import redirect_stdout

from ems.__main__ import main


class CliTests(unittest.TestCase):
    def test_doctor_returns_diagnostic_not_successful_capture(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["doctor"])
        self.assertEqual(code, 0)
        doc = json.loads(output.getvalue())
        self.assertFalse(doc["commercial_approval"])
        self.assertIn("No video capture", doc["message"].replace("no video capture", "No video capture"))


if __name__ == "__main__":
    unittest.main()
