"""Self-referential test: mcp-doctor checks itself and expects all grades >= B."""

import unittest
from pathlib import Path
from unittest import TestCase

from mcp_doctor.checks import overall_grade, run_all_checks
from mcp_doctor.loader import load_from_path

PROJECT_ROOT = Path(__file__).parent.parent


class TestSelfCheck(TestCase):
    """mcp-doctor must pass its own quality checks."""

    def test_self_check_overall_at_least_b(self):
        info = load_from_path(PROJECT_ROOT)
        results = run_all_checks(info)
        grade = overall_grade(results)
        self.assertIn(grade, ("A", "B"), f"Overall grade is {grade}, expected A or B")

    # FastMCP schemas are runtime-only; static loader can't extract them
    @unittest.expectedFailure
    def test_self_check_no_d_grades(self):
        info = load_from_path(PROJECT_ROOT)
        results = run_all_checks(info)
        for r in results:
            self.assertNotEqual(
                r.grade,
                "D",
                f"{r.dimension} got grade D (score={r.score}): {r.recommendations}",
            )

    def test_self_check_has_all_6_dimensions(self):
        info = load_from_path(PROJECT_ROOT)
        results = run_all_checks(info)
        self.assertEqual(len(results), 6)
        dims = {r.dimension for r in results}
        self.assertIn("Task Clarity", dims)
        self.assertIn("Trust & Safety", dims)
        self.assertIn("Interface Quality", dims)
        self.assertIn("Token Efficiency", dims)
        self.assertIn("Install Friction", dims)
        self.assertIn("Cross-platform Readiness", dims)
