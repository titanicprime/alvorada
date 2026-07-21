import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


def load_import_submission_module():
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "import_submission.py"
    spec = importlib.util.spec_from_file_location("import_submission", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load scripts/import_submission.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestImportSubmission(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_import_submission_module()
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)

        (self.repo_root / "state").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "missions" / "ALVORADA_MISSION_002" / "submissions").mkdir(
            parents=True, exist_ok=True
        )

        current_data = {
            "system": "ALVORADA",
            "current_mission": "ALVORADA_MISSION_002",
            "collection_status": "OPEN",
            "members": {"expected": ["MR_GOLD", "BLUE_0", "SIENNA_4"]},
        }
        (self.repo_root / "state" / "current.yaml").write_text(
            yaml.safe_dump(current_data, sort_keys=False),
            encoding="utf-8",
        )

        collection_data = {
            "mission_id": "ALVORADA_MISSION_002",
            "status": "OPEN",
            "expected": ["MR_GOLD", "BLUE_0", "SIENNA_4"],
            "received": [],
            "missing": ["MR_GOLD", "BLUE_0", "SIENNA_4"],
        }
        (self.repo_root / "missions" / "ALVORADA_MISSION_002" / "collection.yaml").write_text(
            yaml.safe_dump(collection_data, sort_keys=False),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_source(self, text: str) -> Path:
        path = self.repo_root / "incoming.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def run_import(
        self,
        member: str = "MR_GOLD",
        mission_id: str = "ALVORADA_MISSION_002",
        source_text: str = "This is a verbatim submission.",
    ) -> tuple[Path, dict]:
        source_file = self.write_source(source_text)
        return self.module.import_submission(
            repo_root=self.repo_root,
            mission_id=mission_id,
            member=member,
            source_file=source_file,
            source_environment="copilot-chat",
            received_at="2026-07-21T08:00:00Z",
            imported_by="andre",
        )

    def test_valid_import(self):
        target_path, _collection = self.run_import(member="MR_GOLD")
        text = target_path.read_text(encoding="utf-8")
        self.assertIn("MISSION_ID: ALVORADA_MISSION_002", text)
        self.assertIn("MEMBER: MR_GOLD", text)
        self.assertIn("STATUS: SUBMITTED_FOR_COLLECTION", text)
        self.assertIn("--- BEGIN VERBATIM SUBMISSION ---", text)
        self.assertIn("This is a verbatim submission.", text)
        self.assertIn("--- END VERBATIM SUBMISSION ---", text)

    def test_member_to_filename_mapping(self):
        target_gold, _ = self.run_import(member="MR_GOLD", source_text="gold")
        self.assertEqual(target_gold.name, "mr-gold.txt")

        target_blue, _ = self.run_import(member="BLUE_0", source_text="blue")
        self.assertEqual(target_blue.name, "blue-0.txt")

        target_sienna, _ = self.run_import(member="SIENNA_4", source_text="sienna")
        self.assertEqual(target_sienna.name, "sienna-4.txt")

    def test_collection_yaml_update(self):
        _target_path, collection = self.run_import(member="BLUE_0")
        self.assertEqual(collection["status"], "OPEN")
        self.assertIn("BLUE_0", collection["received"])
        self.assertNotIn("BLUE_0", collection["missing"])

    def test_source_remains_unchanged(self):
        source_file = self.write_source("Exact content must remain unchanged.")
        before = source_file.read_text(encoding="utf-8")
        self.module.import_submission(
            repo_root=self.repo_root,
            mission_id="ALVORADA_MISSION_002",
            member="MR_GOLD",
            source_file=source_file,
            source_environment="copilot-chat",
            received_at="2026-07-21T08:00:00Z",
            imported_by="andre",
        )
        after = source_file.read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def test_empty_submission_rejection(self):
        with self.assertRaises(self.module.SubmissionImportError):
            self.run_import(source_text="   \n\t")

    def test_invalid_mission_id_rejection(self):
        with self.assertRaises(self.module.SubmissionImportError):
            self.run_import(mission_id="MISSION_002")

    def test_closed_collection_rejection(self):
        collection_path = self.repo_root / "missions" / "ALVORADA_MISSION_002" / "collection.yaml"
        data = yaml.safe_load(collection_path.read_text(encoding="utf-8"))
        data["status"] = "CLOSED"
        collection_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

        with self.assertRaises(self.module.SubmissionImportError):
            self.run_import()

    def test_overwrite_rejection(self):
        self.run_import(member="MR_GOLD", source_text="first")
        with self.assertRaises(self.module.SubmissionImportError):
            self.run_import(member="MR_GOLD", source_text="second")

    def test_obvious_credential_marker_rejection(self):
        with self.assertRaises(self.module.SubmissionImportError):
            self.run_import(source_text="do not store ghp_abcdefghijklmnopqrstuvwxyz")

    def test_no_change_to_state_current_yaml(self):
        current_path = self.repo_root / "state" / "current.yaml"
        before = current_path.read_text(encoding="utf-8")
        self.run_import()
        after = current_path.read_text(encoding="utf-8")
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
