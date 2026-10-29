"""Reproducible App Space end-to-end test against the packaged project interfaces."""
import unittest
from tests.test_app_space import mk_stack, manifest, authz
from app_space import AppStateError, SyncError


class AppSpaceEndToEnd(unittest.TestCase):
    def test_external_event_context_delivery_and_revoke(self):
        _, ledger, registry, bridge, sync = mk_stack()
        registry.register(manifest())
        registry.transition("app.test", "AVAILABLE")
        registry.transition(
            "app.test", "CONNECTED",
            authorization=authz("app-connect", {"app_id": "app.test", "to": "CONNECTED"})
        )

        items = [{"type": "email.received", "id": "e2e-001",
                  "subject": "Entrevista mañana", "provenance": "external"}]
        batch = {"app_id": "app.test", "scope": "gmail.read", "items": items}
        result = sync.sync(
            "app.test", items, authz("app-event-ingest", batch),
            "gmail.read", "tenant-e2e", "owner-e2e", "e2e-correlation"
        )
        self.assertEqual(result["delivered"], 1)
        self.assertEqual(len(bridge.cognitive_twin.external_context_events), 1)
        receipt = bridge.cognitive_twin.external_context_events[0]
        self.assertEqual(receipt["tenant_id"], "tenant-e2e")
        self.assertEqual(receipt["owner_id"], "owner-e2e")
        self.assertFalse(receipt["identity_mutated"])
        self.assertFalse(receipt["truth_promoted"])
        self.assertEqual(receipt["context"]["external_event_is_identity"], False)
        self.assertTrue(registry.apps["app.test"].verify_content_hash())
        self.assertTrue(ledger.verify())

        sync.revoke("app.test")
        self.assertEqual(registry.apps["app.test"].status, "REVOKED")
        raw = items[0]
        raw_auth = authz("app-event-ingest",
                         {"app_id": "app.test", "scope": "gmail.read", "raw": raw})
        with self.assertRaises(AppStateError):
            bridge.ingest(app_id="app.test", scope="gmail.read", raw_event=raw,
                          authorization=raw_auth, tenant_id="tenant-e2e",
                          owner_id="owner-e2e")
        with self.assertRaises(SyncError):
            sync.sync("app.test", items, authz("app-event-ingest", batch),
                      "gmail.read", "tenant-e2e", "owner-e2e")
        self.assertTrue(ledger.verify())


if __name__ == "__main__":
    unittest.main(verbosity=2)
