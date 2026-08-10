#!/usr/bin/env python3

import unittest
from pathlib import Path

from policy import flow_allowed, identity_allowed, load_policy, scope_contains


POLICY = load_policy(Path(__file__).with_name("access_policy.json"))
VAULT = "/subscriptions/sub-42/resourceGroups/rg-prod/providers/Microsoft.KeyVault/vaults/kv-prod"


class PolicyTest(unittest.TestCase):
    def test_scope_boundary_prevents_prefix_confusion(self) -> None:
        self.assertTrue(scope_contains("/groups/prod", "/groups/prod/apps/api"))
        self.assertFalse(scope_contains("/groups/prod", "/groups/production"))

    def test_managed_identity_reads_only_its_vault_secret(self) -> None:
        self.assertTrue(
            identity_allowed(POLICY, "api-prod-mi", "Microsoft.KeyVault/vaults/secrets/read", VAULT + "/secrets/db")
        )
        self.assertFalse(
            identity_allowed(POLICY, "api-prod-mi", "Microsoft.KeyVault/vaults/secrets/write", VAULT + "/secrets/db")
        )
        self.assertFalse(
            identity_allowed(POLICY, "api-prod-mi", "Microsoft.KeyVault/vaults/secrets/read", VAULT + "-backup/secrets/db")
        )

    def test_deployer_cannot_assign_roles(self) -> None:
        self.assertFalse(
            identity_allowed(
                POLICY,
                "deploy-prod-oidc",
                "Microsoft.Authorization/roleAssignments/write",
                "/subscriptions/sub-42/resourceGroups/rg-prod",
            )
        )

    def test_https_private_endpoint_flow(self) -> None:
        self.assertTrue(flow_allowed(POLICY, "10.42.1.18", "10.42.3.4", "tcp", 443))
        self.assertFalse(flow_allowed(POLICY, "10.42.1.18", "10.42.3.4", "tcp", 80))

    def test_database_flow_is_source_restricted(self) -> None:
        self.assertTrue(flow_allowed(POLICY, "10.42.2.9", "10.42.4.25", "tcp", 5432))
        self.assertFalse(flow_allowed(POLICY, "10.42.1.9", "10.42.4.25", "tcp", 5432))

    def test_everything_else_is_denied(self) -> None:
        self.assertFalse(flow_allowed(POLICY, "198.51.100.8", "10.42.3.4", "tcp", 443))
        self.assertFalse(identity_allowed(POLICY, "unknown", "read", VAULT))


if __name__ == "__main__":
    unittest.main(verbosity=2)
