import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from validate_manifest import validate


HERE = Path(__file__).parent


class ManifestValidationTest(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((HERE / "run-manifest.json").read_text())

    def test_reference_manifest_passes(self):
        self.assertEqual([], validate(self.manifest, HERE))

    def test_split_overlap_is_rejected(self):
        bad = copy.deepcopy(self.manifest)
        bad["splits"]["test"].append("C1001")
        self.assertTrue(any("split leakage" in e for e in validate(bad, HERE)))

    def test_mutable_registry_alias_is_rejected(self):
        bad = copy.deepcopy(self.manifest)
        bad["model"]["registry_uri"] = "models:/claims-risk/production"
        self.assertTrue(any("numeric immutable" in e for e in validate(bad, HERE)))

    def test_failing_quality_gate_is_rejected(self):
        bad = copy.deepcopy(self.manifest)
        bad["metrics"]["test_auc"] = 0.87
        self.assertTrue(any("quality gate failed" in e for e in validate(bad, HERE)))

    def test_secret_key_is_rejected(self):
        bad = copy.deepcopy(self.manifest)
        bad["tracking_token"] = "do-not-store-me"
        self.assertTrue(any("sensitive key" in e for e in validate(bad, HERE)))

    def test_tampered_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "model.json").write_text("tampered")
            bad = copy.deepcopy(self.manifest)
            self.assertTrue(any("digest mismatch" in e for e in validate(bad, root)))


if __name__ == "__main__":
    unittest.main()
