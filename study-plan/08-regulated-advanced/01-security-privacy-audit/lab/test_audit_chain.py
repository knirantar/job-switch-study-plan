import copy, unittest
from audit_chain import append, verify

BASE = {"timestamp":"2026-08-09T10:15:00Z","actor_id":"usr_7f3a","action":"MODEL_APPROVE",
        "resource_id":"model_claims_17","decision":"ALLOW"}

class AuditChainTest(unittest.TestCase):
    def setUp(self):
        self.chain=[]; append(self.chain, BASE); append(self.chain, {**BASE,"action":"MODEL_DEPLOY"})

    def test_valid_chain(self): self.assertEqual([], verify(self.chain))
    def test_modified_event_detected(self):
        bad=copy.deepcopy(self.chain); bad[0]["decision"]="DENY"
        self.assertTrue(any("content changed" in e for e in verify(bad)))
    def test_deleted_event_detected(self):
        bad=copy.deepcopy(self.chain); del bad[0]
        self.assertTrue(verify(bad))
    def test_reordered_event_detected(self):
        bad=list(reversed(copy.deepcopy(self.chain)))
        self.assertTrue(verify(bad))
    def test_sensitive_field_rejected(self):
        with self.assertRaises(ValueError): append([], {**BASE,"access_token":"abc"})
    def test_added_field_detected(self):
        bad=copy.deepcopy(self.chain); bad[0]["debug"]="x"
        self.assertTrue(any("wrong fields" in e for e in verify(bad)))

if __name__ == "__main__": unittest.main()
