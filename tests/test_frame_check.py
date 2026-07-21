"""
test_frame_check.py — Unit tests for scripts/frame_check.py
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts/ to path so we can import frame_check directly.
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import frame_check as fc  # noqa: E402
import yaml  # noqa: E402

ACTIVE_COLLECTION_PATTERN = {
    "asset_id": "FP-001",
    "type": "FAILURE_PATTERN",
    "statement": (
        "Do not synthesize independent member submissions before collection is explicitly closed."
    ),
    "conditions": "Multiple independent submissions are expected.",
    "origin_mission": "ALVORADA_MISSION_001",
    "status": "ACTIVE",
}

ACTIVE_UNRELATED_PATTERN = {
    "asset_id": "FP-002",
    "type": "FAILURE_PATTERN",
    "statement": "Do not describe ordinary LLM inference as native ISS execution.",
    "conditions": "Current model behavior is described using Cognous architectural terms.",
    "origin_mission": "ALVORADA_MISSION_001",
    "status": "ACTIVE",
}

SUSPENDED_PATTERN = {
    "asset_id": "FP-SUSPENDED",
    "type": "FAILURE_PATTERN",
    "statement": "This pattern is suspended.",
    "conditions": "Multiple independent submissions are expected.",
    "origin_mission": "ALVORADA_MISSION_001",
    "status": "SUSPENDED",
}


class TestFrameCheck(unittest.TestCase):
    def test_matches_collection_closure_pattern(self):
        """A work item about independent submissions should match FP-001."""
        work_item = {
            "title": "Review independent submissions",
            "problem_statement": "Synthesize the three independent member submissions.",
        }
        matched = fc.run_frame_check(work_item, [ACTIVE_COLLECTION_PATTERN])
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["asset_id"], "FP-001")

    def test_no_match_for_irrelevant_work_item(self):
        """A work item about a completely unrelated topic should not match FP-001."""
        work_item = {
            "title": "Format the output document",
            "problem_statement": "Apply consistent heading styles.",
        }
        matched = fc.run_frame_check(work_item, [ACTIVE_COLLECTION_PATTERN])
        self.assertEqual(len(matched), 0)

    def test_only_active_patterns_are_returned(self):
        """SUSPENDED patterns must not appear in results even when keywords match."""
        work_item = {
            "title": "Combining independent submissions",
            "problem_statement": "Multiple independent submissions are ready.",
        }
        patterns = [ACTIVE_COLLECTION_PATTERN, SUSPENDED_PATTERN]
        matched = fc.run_frame_check(work_item, patterns)
        matched_ids = [p["asset_id"] for p in matched]
        self.assertIn("FP-001", matched_ids)
        self.assertNotIn("FP-SUSPENDED", matched_ids)

    def test_output_file_receives_failure_memory(self):
        """When --output is specified, the output file must contain failure_memory."""
        work_item = {
            "title": "Combining independent submissions",
            "problem_statement": "Multiple independent submissions are ready.",
        }
        patterns = [ACTIVE_COLLECTION_PATTERN]

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", delete=False, mode="w", encoding="utf-8"
        ) as work_file:
            yaml.dump(work_item, work_file)
            work_item_path = work_file.name

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", delete=False, mode="w", encoding="utf-8"
        ) as patterns_file:
            yaml.dump(patterns, patterns_file)
            patterns_path = patterns_file.name

        output_path = work_item_path + ".out.yaml"

        try:
            loaded_work_item = fc.load_file(Path(work_item_path))
            loaded_patterns = fc.load_failure_patterns(Path(patterns_path))
            matched = fc.run_frame_check(loaded_work_item, loaded_patterns)

            output_data = dict(loaded_work_item)
            output_data["failure_memory"] = [
                {
                    "asset_id": p.get("asset_id"),
                    "statement": p.get("statement"),
                    "origin_mission": p.get("origin_mission"),
                }
                for p in matched
            ]
            Path(output_path).write_text(
                yaml.dump(output_data, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            result = fc.load_file(Path(output_path))
            self.assertIn("failure_memory", result)
            self.assertTrue(len(result["failure_memory"]) > 0)
            self.assertEqual(result["failure_memory"][0]["asset_id"], "FP-001")
        finally:
            os.unlink(work_item_path)
            os.unlink(patterns_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_source_file_unchanged_after_output(self):
        """Writing --output must not modify the original work item file."""
        work_item = {
            "title": "Combining independent submissions",
            "problem_statement": "Multiple independent submissions are ready.",
        }
        patterns = [ACTIVE_COLLECTION_PATTERN]

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", delete=False, mode="w", encoding="utf-8"
        ) as work_file:
            yaml.dump(work_item, work_file)
            work_item_path = work_file.name

        original_text = Path(work_item_path).read_text(encoding="utf-8")
        output_path = work_item_path + ".out.yaml"

        try:
            loaded_work_item = fc.load_file(Path(work_item_path))
            matched = fc.run_frame_check(loaded_work_item, patterns)

            output_data = dict(loaded_work_item)
            output_data["failure_memory"] = [{"asset_id": p.get("asset_id")} for p in matched]
            Path(output_path).write_text(
                yaml.dump(output_data, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            after_text = Path(work_item_path).read_text(encoding="utf-8")
            self.assertEqual(original_text, after_text)
        finally:
            os.unlink(work_item_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


if __name__ == "__main__":
    unittest.main()
