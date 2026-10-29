import unittest

from app_space import (
    AppManifest,
    AppRegistry,
    AppSpaceError,
    CognitiveTwinContextPort,
    ScopeViolation,
    _sanitize_external_payload,
)
from feedback_loop import FeedbackLoop, PreferenceObservation
from swarm import SafetyImmutable, Swarm, TrustRampViolation, UnknownCapability


def make_manifest(**overrides):
    fields = {
        "app_id": "app.test",
        "name": "Test",
        "display_name": "Test app",
        "version": "1.0",
        "type": "EXTERNAL",
        "category": "test",
        "provider": "test",
        "source": "test",
        "native_or_external": "external",
        "capabilities": ("read",),
        "permissions": ("READ_EMAIL",),
        "scopes": ("gmail.read",),
        "data_types": ("email",),
        "supported_platforms": ("web",),
        "connector": "test",
        "sync_policy": {"mode": "incremental"},
        "privacy_classification": "private",
        "provenance": "SYSTEM_DERIVED",
    }
    fields.update(overrides)
    return AppManifest(**fields)


class FeedbackLoopTests(unittest.TestCase):
    def test_feedback_only_proposes_and_inferred_needs_evidence(self):
        result = FeedbackLoop().run({"decision_id": "d1"}, "ok", "helpful")
        self.assertEqual(result["identity_direct_modification"], "PROHIBITED")
        self.assertFalse(result["auto_apply"])
        self.assertIn("PROPOSAL", result["possible_evolution"])
        with self.assertRaises(ValueError):
            PreferenceObservation("coffee", "INFERRED", "prefers coffee", 0.8)


class SwarmTests(unittest.TestCase):
    def test_trust_promotion_requires_distinct_evidence(self):
        swarm = Swarm()
        agent = swarm.spawn("agent-1", "reflection", "synthesize", ["synthesize"])
        self.assertEqual(agent.trust, "shadow")
        with self.assertRaises(UnknownCapability):
            swarm.spawn("agent-2", "reflection", "x", ["admin"])
        for index in range(3):
            swarm.record_correct_execution("agent-1", f"evidence:{index}")
        self.assertEqual(swarm.promote("agent-1"), "approval")
        with self.assertRaises(TrustRampViolation):
            swarm.record_correct_execution("agent-1", "evidence:2")

    def test_safety_rules_require_confirmation_and_revoke_disables_capabilities(self):
        swarm = Swarm()
        swarm.spawn("safety-1", "safety", "veto", ["veto"])
        with self.assertRaises(SafetyImmutable):
            swarm.modify_safety_rules("safety-1", {"limits": ("updated",)})
        swarm.modify_safety_rules(
            "safety-1", {"limits": ("updated",)}, human_confirmed=True
        )
        self.assertEqual(swarm.status("safety-1").limits, ("updated",))
        swarm.revoke("safety-1")
        self.assertFalse(swarm.check("safety-1", "veto"))


class AppSpaceTests(unittest.TestCase):
    def test_manifest_hash_and_scope_permission_binding(self):
        manifest = make_manifest()
        original_hash = manifest.content_hash
        manifest.status = "AVAILABLE"
        self.assertFalse(manifest.verify_content_hash())
        manifest.refresh_content_hash()
        self.assertNotEqual(manifest.content_hash, original_hash)
        self.assertTrue(manifest.verify_content_hash())
        with self.assertRaises(ScopeViolation):
            make_manifest(scopes=("gmail.send",))

    def test_connect_fails_closed_for_unverifiable_authorization(self):
        registry = AppRegistry(policy=None)
        registry.configure_authority("did:example:authority", "2026-10-29")
        manifest = registry.register(make_manifest())
        registry.transition(manifest.app_id, "AVAILABLE")
        with self.assertRaises(AppSpaceError):
            registry.transition(
                manifest.app_id, "CONNECTED", authorization="authorized=True"
            )
        self.assertEqual(manifest.status, "AVAILABLE")
        self.assertTrue(manifest.verify_content_hash())

    def test_external_context_is_not_identity_or_truth(self):
        port = CognitiveTwinContextPort()
        event = {
            "content_hash": "event-hash",
            "tenant_id": "YO",
            "owner_id": "owner",
            "provenance": "OBSERVED",
        }
        context = {
            "tenant_id": "YO",
            "owner_id": "owner",
            "external_event_is_identity": False,
            "external_data_is_truth": False,
        }
        receipt = port.ingest_context(context, event=event)
        self.assertTrue(receipt["accepted"])
        self.assertFalse(port.external_context_events[0]["identity_mutated"])
        with self.assertRaises(ValueError):
            port.ingest_context(
                {**context, "tenant_id": "ELLA"}, event=event
            )

    def test_external_identity_claims_are_removed(self):
        clean = _sanitize_external_payload(
            {"identity": "trusted", "value": "claimed", "message": "hello"}
        )
        self.assertNotIn("identity", clean)
        self.assertNotIn("value", clean)
        self.assertTrue(clean["untrusted_identity_claim_removed"])
        self.assertEqual(clean["message"], "hello")


if __name__ == "__main__":
    unittest.main()
