import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


def load_create_mission_module():
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "create_mission.py"
    spec = importlib.util.spec_from_file_location("create_mission", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load scripts/create_mission.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCreateMission(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_create_mission_module()
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        (self.repo_root / "state").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "missions").mkdir(parents=True, exist_ok=True)

        current = {
            "system": "ALVORADA",
            "current_mission": None,
            "collection_status": "CLOSED",
            "members": {"expected": ["MR_GOLD", "BLUE_0", "SIENNA_4"]},
        }
        (self.repo_root / "state" / "current.yaml").write_text(
            yaml.safe_dump(current, sort_keys=False),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_valid_mission_creation(self):
        self.module.create_mission(
            self.repo_root,
            "ALVORADA_MISSION_002",
            "Pilot mission",
            "What should we test next?",
        )

        mission_dir = self.repo_root / "missions" / "ALVORADA_MISSION_002"
        self.assertTrue((mission_dir / "mission.md").exists())
        self.assertTrue((mission_dir / "collection.yaml").exists())
        self.assertTrue((mission_dir / "submissions" / ".gitkeep").exists())

    def test_invalid_mission_id(self):
        with self.assertRaises(self.module.MissionError):
            self.module.create_mission(
                self.repo_root,
                "MISSION_002",
                "Invalid ID mission",
                "Should fail?",
            )

    def test_refuses_to_overwrite_existing_mission(self):
        self.module.create_mission(
            self.repo_root,
            "ALVORADA_MISSION_003",
            "First create",
            "Question one?",
        )
        with self.assertRaises(self.module.MissionError):
            self.module.create_mission(
                self.repo_root,
                "ALVORADA_MISSION_003",
                "Second create",
                "Question two?",
            )

    def test_collection_initialization(self):
        mission_id = "ALVORADA_MISSION_004"
        self.module.create_mission(self.repo_root, mission_id, "Title", "Question?")
        collection_path = self.repo_root / "missions" / mission_id / "collection.yaml"
        collection = yaml.safe_load(collection_path.read_text(encoding="utf-8"))

        self.assertEqual(collection["mission_id"], mission_id)
        self.assertEqual(collection["status"], "OPEN")
        self.assertEqual(collection["expected"], ["MR_GOLD", "BLUE_0", "SIENNA_4"])
        self.assertEqual(collection["received"], [])
        self.assertEqual(collection["missing"], ["MR_GOLD", "BLUE_0", "SIENNA_4"])

    def test_current_yaml_update(self):
        mission_id = "ALVORADA_MISSION_005"
        self.module.create_mission(self.repo_root, mission_id, "Title", "Question?")
        current_path = self.repo_root / "state" / "current.yaml"
        current = yaml.safe_load(current_path.read_text(encoding="utf-8"))

        self.assertEqual(current["current_mission"], mission_id)
        self.assertEqual(current["collection_status"], "OPEN")


if __name__ == "__main__":
    unittest.main()
