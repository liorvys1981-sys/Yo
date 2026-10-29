import sys, unittest, tempfile, os, json, hashlib
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "APP_YO" / "app_space"))
_EL_ROOT = _ROOT / "EL_YO"
for _candidate in _EL_ROOT.rglob("*"):
    if _candidate.is_dir():
        sys.path.insert(0, str(_candidate))
sys.path.insert(0, '/mnt/agents/output/APP_YO/app_space')
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from app_space import (AppManifest, AppRegistry, AppBridge, SyncEngine, AppEvent,
    AppSpaceError, ScopeViolation, AppStateError, SyncError, PERMISSIONS, SCOPES,
    YO_NATIVE_APPS, APP_TYPES, APP_STATES)
from authority import Authority
from identity import Identity
from el_yo.gates import AuthorizationGate, DailyCodeProvider
from el_yo.evidence import EvidenceLedger
from relationship_model import PolicyEngine

KEY = b"g" * 32; TODAY = "2026-10-07"
AUTH = Identity(seed=b"a" * 32)
GATE = AuthorizationGate(DailyCodeProvider(KEY), TODAY, True)
CODE = DailyCodeProvider(KEY).code(TODAY)
_canon = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":")).encode()
_chash = lambda o: hashlib.sha256(_canon(o)).hexdigest()


def manifest(**kw):
    base = dict(app_id="app.test", name="Test", display_name="Test App", version="1.0.0",
                type="EXTERNAL", category="test", provider="test", source="test",
                native_or_external="external", capabilities=("x",),
                permissions=("READ_EMAIL",), scopes=("gmail.read",),
                data_types=("email",), supported_platforms=("web",),
                connector="test_connector", sync_policy={"mode": "incremental"},
                privacy_classification="private", provenance="SYSTEM_DERIVED")
    base.update(kw)
    return AppManifest(**base)


def mk_stack():
    tmp = tempfile.mkdtemp()
    led = EvidenceLedger(os.path.join(tmp, "ledger.jsonl"))
    reg = AppRegistry(PolicyEngine(), ledger=led, clock=lambda: 1.0)
    reg.configure_authority(AUTH.did, TODAY)
    bridge = AppBridge(reg, PolicyEngine(), ledger=led, clock=lambda: 1.0)
    sync = SyncEngine(bridge, ledger=led, clock=lambda: 1.0)
    return tmp, led, reg, bridge, sync


def authz(action, content):
    return Authority(AUTH, GATE, TODAY).authorize_action(
        action, "externa_irreversible", f"EJECUTA appspace {CODE}",
        content_hash=_chash(content))


class TestManifest(unittest.TestCase):
    def test_campos_completos(self):
        m = manifest()
        for c in ("app_id","name","display_name","version","type","category","provider",
                  "source","native_or_external","capabilities","permissions","scopes",
                  "data_types","supported_platforms","connector","sync_policy",
                  "privacy_classification","provenance","status","content_hash"):
            self.assertTrue(hasattr(m, c), c)
        self.assertEqual(len(m.content_hash), 64)
        self.assertEqual(m.status, "DISCOVERED")

    def test_tipos_y_estados(self):
        for t in APP_TYPES:
            manifest(type=t)
        m = manifest(status="CONNECTED")
        self.assertEqual(m.status, "CONNECTED")
        with self.assertRaises(AppSpaceError):
            manifest(type="FANTASMA")
        with self.assertRaises(AppSpaceError):
            manifest(status="ACTIVA")

    def test_wildcard_scope_prohibido(self):
        with self.assertRaises(ScopeViolation):
            manifest(scopes=("*",))

    def test_permisos_y_scopes_desconocidos(self):
        with self.assertRaises(AppSpaceError):
            manifest(permissions=("READ_ALMA",))
        with self.assertRaises(AppSpaceError):
            manifest(scopes=("gmail.admin",))


class TestRegistryStates(unittest.TestCase):
    def test_maquina_de_estados(self):
        _, _, reg, _, _ = mk_stack()
        reg.register(manifest())
        reg.transition("app.test", "AVAILABLE")
        with self.assertRaises(AppStateError):
            reg.transition("app.test", "PAUSED")      # AVAILABLE -> PAUSED prohibido
        reg.transition("app.test", "CONNECTED",
                      authorization=authz("app-connect", {"app_id": "app.test", "to": "CONNECTED"}))
        reg.transition("app.test", "PAUSED")
        reg.transition("app.test", "REVOKED")
        with self.assertRaises(AppStateError):
            reg.transition("app.test", "CONNECTED")   # REVOKED terminal

    def test_connect_sin_autorizacion(self):
        _, _, reg, _, _ = mk_stack()
        reg.register(manifest())
        reg.transition("app.test", "AVAILABLE")
        with self.assertRaises(AppSpaceError):
            reg.transition("app.test", "CONNECTED")


class TestBridge(unittest.TestCase):
    def test_pipeline_externo(self):
        tmp, led, reg, bridge, _ = mk_stack()
        reg.register(manifest())
        reg.transition("app.test", "AVAILABLE")
        reg.transition("app.test", "CONNECTED",
                      authorization=authz("app-connect", {"app_id": "app.test", "to": "CONNECTED"}))
        raw = {"type": "email.received", "from": "a@b.c", "subject": "hola"}
        content = {"app_id": "app.test", "scope": "gmail.read", "raw": raw}
        out = bridge.ingest(app_id="app.test", scope="gmail.read", raw_event=raw,
                            authorization=authz("app-event-ingest", content),
                            tenant_id="YO", owner_id="yo", correlation_id="c1")
        ev = out["event"]
        self.assertEqual(len(ev.content_hash), 64)
        self.assertEqual(ev.permission_scope, "gmail.read")
        self.assertEqual(ev.provenance, "OBSERVED")
        self.assertFalse(out["is_fact"])
        self.assertFalse(out["is_identity"])
        self.assertIn("EXTERNAL EVENT != IDENTITY", out["note"])
        self.assertTrue(led.verify())

    def test_scope_no_declarado(self):
        tmp, led, reg, bridge, _ = mk_stack()
        reg.register(manifest())
        reg.transition("app.test", "AVAILABLE")
        reg.transition("app.test", "CONNECTED",
                      authorization=authz("app-connect", {"app_id": "app.test", "to": "CONNECTED"}))
        raw = {"type": "x"}
        content = {"app_id": "app.test", "scope": "drive.write", "raw": raw}
        with self.assertRaises(ScopeViolation):
            bridge.ingest(app_id="app.test", scope="drive.write", raw_event=raw,
                          authorization=authz("app-event-ingest", content),
                          tenant_id="YO", owner_id="yo")

    def test_ingest_paused_rechazado(self):
        tmp, led, reg, bridge, _ = mk_stack()
        reg.register(manifest())
        reg.transition("app.test", "AVAILABLE")
        reg.transition("app.test", "CONNECTED",
                      authorization=authz("app-connect", {"app_id": "app.test", "to": "CONNECTED"}))
        reg.transition("app.test", "PAUSED")
        raw = {"type": "x"}
        content = {"app_id": "app.test", "scope": "gmail.read", "raw": raw}
        with self.assertRaises(AppStateError):
            bridge.ingest(app_id="app.test", scope="gmail.read", raw_event=raw,
                          authorization=authz("app-event-ingest", content),
                          tenant_id="YO", owner_id="yo")


class TestSync(unittest.TestCase):
    def _connected(self):
        tmp, led, reg, bridge, sync = mk_stack()
        reg.register(manifest())
        reg.transition("app.test", "AVAILABLE")
        reg.transition("app.test", "CONNECTED",
                      authorization=authz("app-connect", {"app_id": "app.test", "to": "CONNECTED"}))
        return tmp, led, reg, bridge, sync

    def test_sync_cursor_dedup_checkpoint(self):
        tmp, led, reg, bridge, sync = self._connected()
        items = [{"type": "email.received", "id": str(i)} for i in range(3)]
        content = {"app_id": "app.test", "scope": "gmail.read", "items": items}
        az = authz("app-event-ingest", content)
        r1 = sync.sync("app.test", items, az, "gmail.read", "YO", "yo")
        self.assertEqual(r1["delivered"], 3)
        self.assertNotEqual(r1["cursor"], "GENESIS")
        r2 = sync.sync("app.test", items, az, "gmail.read", "YO", "yo")   # idempotencia
        self.assertEqual(r2["delivered"], 0)
        self.assertEqual(r2["duplicates"], 3)
        self.assertEqual(r2["from_cursor"], r1["cursor"])                 # checkpoint

    def test_conflict_detection(self):
        tmp, led, reg, bridge, sync = self._connected()
        items = [{"type": "x", "id": "c1", "conflict": True}]
        content = {"app_id": "app.test", "scope": "gmail.read", "items": items}
        az = authz("app-event-ingest", content)
        r = sync.sync("app.test", [{"type": "x", "id": "k", "conflict": True}],
                      az, "gmail.read", "YO", "yo")
        self.assertEqual(r["delivered"], 0)
        self.assertEqual(r["conflicts"], 1)

    def test_pause_resume_revoke(self):
        tmp, led, reg, bridge, sync = self._connected()
        raw = {"type": "x", "id": "p1"}
        items = [raw]
        content = {"app_id": "app.test", "scope": "gmail.read", "items": items}
        az = authz("app-event-ingest", content)
        sync.pause("app.test")
        with self.assertRaises(SyncError):
            sync.sync("app.test", [raw], az, "gmail.read", "YO", "yo")
        sync.resume("app.test")
        r = sync.sync("app.test", [raw], az, "gmail.read", "YO", "yo")
        self.assertEqual(r["delivered"], 1)
        sync.revoke("app.test")
        with self.assertRaises(SyncError):
            sync.sync("app.test", [raw], az, "gmail.read", "YO", "yo")
        self.assertNotIn("app.test", sync.cursors)


class TestNativeApps(unittest.TestCase):
    def test_ocho_apps_nativas(self):
        self.assertEqual(len(YO_NATIVE_APPS), 8)
        for spec in YO_NATIVE_APPS:
            self.assertEqual(spec["type"], "NATIVE_YO")
            self.assertTrue(spec["app_id"].startswith("yo."))
            self.assertTrue(set(spec["scopes"]) <= set(SCOPES.keys()))

    def test_read_no_implica_write(self):
        m = manifest(permissions=("READ_EMAIL",), scopes=("gmail.read",))
        self.assertNotIn("WRITE_EMAIL", m.permissions)
        self.assertNotIn("gmail.send", m.scopes)


class TestSecurityAttacks(unittest.TestCase):
    def _connected(self):
        tmp, led, reg, bridge, sync = mk_stack()
        reg.register(manifest())
        reg.transition("app.test", "AVAILABLE")
        reg.transition("app.test", "CONNECTED",
                      authorization=authz("app-connect", {"app_id": "app.test", "to": "CONNECTED"}))
        return tmp, led, reg, bridge, sync

    def test_write_usando_read_scope(self):
        tmp, led, reg, bridge, sync = self._connected()
        raw = {"type": "email.sent"}
        content = {"app_id": "app.test", "scope": "gmail.send", "raw": raw}
        with self.assertRaises(ScopeViolation):   # app solo declaro gmail.read
            bridge.ingest(app_id="app.test", scope="gmail.send", raw_event=raw,
                          authorization=authz("app-event-ingest", content),
                          tenant_id="YO", owner_id="yo")

    def test_undeclared_app(self):
        _, _, reg, bridge, _ = mk_stack()
        raw = {"type": "x"}
        content = {"app_id": "app.evil", "scope": "gmail.read", "raw": raw}
        with self.assertRaises(AppSpaceError):
            bridge.ingest(app_id="app.evil", scope="gmail.read", raw_event=raw,
                          authorization=authz("app-event-ingest", content),
                          tenant_id="YO", owner_id="yo")

    def test_forged_auth(self):
        tmp, led, reg, bridge, _ = self._connected()
        raw = {"type": "x"}
        with self.assertRaises(AppSpaceError):
            bridge.ingest(app_id="app.test", scope="gmail.read", raw_event=raw,
                          authorization="authorized=True",
                          tenant_id="YO", owner_id="yo")

    def test_replay_ingest(self):
        tmp, led, reg, bridge, _ = self._connected()
        raw = {"type": "email.received", "id": "r1"}
        content = {"app_id": "app.test", "scope": "gmail.read", "raw": raw}
        az = authz("app-event-ingest", content)
        bridge.ingest(app_id="app.test", scope="gmail.read", raw_event=raw,
                      authorization=az, tenant_id="YO", owner_id="yo")
        raw2 = {"type": "email.received", "id": "r2"}
        with self.assertRaises(AppSpaceError):   # misma authz, contenido distinto
            bridge.ingest(app_id="app.test", scope="gmail.read", raw_event=raw2,
                          authorization=az, tenant_id="YO", owner_id="yo")

    def test_revoked_impede_new_ops(self):
        tmp, led, reg, bridge, sync = self._connected()
        reg.transition("app.test", "REVOKED")
        raw = {"type": "x", "id": "v1"}
        content = {"app_id": "app.test", "scope": "gmail.read", "raw": raw}
        with self.assertRaises(AppStateError):
            bridge.ingest(app_id="app.test", scope="gmail.read", raw_event=raw,
                          authorization=authz("app-event-ingest", content),
                          tenant_id="YO", owner_id="yo")

    def test_wildcard_scope(self):
        with self.assertRaises(ScopeViolation):
            manifest(scopes=("*",))

    def test_privilege_escalation_app_to_app(self):
        tmp, led, reg, bridge, _ = mk_stack()
        reg.register(manifest())
        reg.register(manifest(app_id="app.other", scopes=("drive.write",),
                              permissions=("WRITE_FILES",)))
        reg.transition("app.test", "AVAILABLE")
        reg.transition("app.test", "CONNECTED",
                      authorization=authz("app-connect", {"app_id": "app.test", "to": "CONNECTED"}))
        raw = {"type": "x"}
        # permiso de app.other NO usable desde app.test
        content = {"app_id": "app.test", "scope": "drive.write", "raw": raw}
        with self.assertRaises(ScopeViolation):
            bridge.ingest(app_id="app.test", scope="drive.write", raw_event=raw,
                          authorization=authz("app-event-ingest", content),
                          tenant_id="YO", owner_id="yo")


class TestAppSpaceHardening(unittest.TestCase):
    def _connected(self):
        tmp, led, reg, bridge, sync = mk_stack()
        reg.register(manifest())
        reg.transition("app.test", "AVAILABLE")
        reg.transition("app.test", "CONNECTED",
                       authorization=authz("app-connect", {"app_id": "app.test", "to": "CONNECTED"}))
        return tmp, led, reg, bridge, sync

    def test_scope_requires_matching_permission(self):
        with self.assertRaises(ScopeViolation):
            manifest(permissions=("READ_EMAIL",), scopes=("gmail.send",))

    def test_manifest_hash_tracks_status_transition(self):
        _, _, reg, _, _ = mk_stack()
        m = manifest()
        reg.register(m)
        first_hash = m.content_hash
        reg.transition("app.test", "AVAILABLE")
        self.assertNotEqual(first_hash, m.content_hash)
        self.assertTrue(m.verify_content_hash())
        reg.transition("app.test", "CONNECTED",
                       authorization=authz("app-connect", {"app_id": "app.test", "to": "CONNECTED"}))
        self.assertTrue(m.verify_content_hash())

    def test_sync_delivered_means_twin_received(self):
        _, _, _, bridge, sync = self._connected()
        items = [{"type": "email.received", "id": "delivery-1"}]
        batch = {"app_id": "app.test", "scope": "gmail.read", "items": items}
        result = sync.sync("app.test", items,
                           authz("app-event-ingest", batch),
                           "gmail.read", "YO", "yo")
        self.assertEqual(result["delivered"], 1)
        self.assertEqual(len(bridge.cognitive_twin.external_context_events), 1)
        receipt = bridge.cognitive_twin.external_context_events[0]
        self.assertFalse(receipt["identity_mutated"])
        self.assertFalse(receipt["truth_promoted"])
        self.assertEqual(receipt["tenant_id"], "YO")

    def test_revoke_blocks_sync_and_direct_bridge(self):
        _, _, reg, bridge, sync = self._connected()
        items = [{"type": "email.received", "id": "revoked-1"}]
        sync.revoke("app.test")
        self.assertEqual(reg.apps["app.test"].status, "REVOKED")
        self.assertTrue(reg.apps["app.test"].verify_content_hash())
        batch = {"app_id": "app.test", "scope": "gmail.read", "items": items}
        raw = items[0]
        with self.assertRaises(SyncError):
            sync.sync("app.test", items, authz("app-event-ingest", batch),
                      "gmail.read", "YO", "yo")
        raw_content = {"app_id": "app.test", "scope": "gmail.read", "raw": raw}
        with self.assertRaises(AppStateError):
            bridge.ingest(app_id="app.test", scope="gmail.read", raw_event=raw,
                          authorization=authz("app-event-ingest", raw_content),
                          tenant_id="YO", owner_id="yo")

    def test_missing_twin_sink_not_counted_as_delivered(self):
        _, _, _, bridge, sync = self._connected()
        bridge.cognitive_twin = None
        items = [{"type": "email.received", "id": "blocked-delivery"}]
        batch = {"app_id": "app.test", "scope": "gmail.read", "items": items}
        with self.assertRaises(AppSpaceError):
            sync.sync("app.test", items, authz("app-event-ingest", batch),
                      "gmail.read", "YO", "yo")
        self.assertNotIn(hashlib.sha256(_canon(items[0])).hexdigest()[:16],
                         sync.seen["app.test"])

    def test_batch_authorization_cannot_be_reused_for_foreign_event(self):
        _, _, _, bridge, _ = self._connected()
        authorized_items = [{"type": "email.received", "id": "allowed"}]
        batch = {"app_id": "app.test", "scope": "gmail.read", "items": authorized_items}
        az = authz("app-event-ingest", batch)
        foreign = {"type": "email.received", "id": "not-in-batch"}
        with self.assertRaises(AppSpaceError):
            bridge.ingest(app_id="app.test", scope="gmail.read", raw_event=foreign,
                          authorization=az, tenant_id="YO", owner_id="yo",
                          batch_hash=hashlib.sha256(_canon(batch)).hexdigest(),
                          batch_items=authorized_items)

    def test_event_content_hash_binds_normalized_payload(self):
        _, _, _, bridge, _ = self._connected()
        raw_a = {"type": "email.received", "id": "payload-a"}
        batch_a = {"app_id": "app.test", "scope": "gmail.read", "items": [raw_a]}
        out_a = bridge.ingest(app_id="app.test", scope="gmail.read", raw_event=raw_a,
                              authorization=authz("app-event-ingest", {
                                  "app_id": "app.test", "scope": "gmail.read", "raw": raw_a}),
                              tenant_id="YO", owner_id="yo")
        raw_b = {"type": "email.received", "id": "payload-b"}
        out_b = bridge.ingest(app_id="app.test", scope="gmail.read", raw_event=raw_b,
                              authorization=authz("app-event-ingest", {
                                  "app_id": "app.test", "scope": "gmail.read", "raw": raw_b}),
                              tenant_id="YO", owner_id="yo")
        self.assertNotEqual(out_a["event"].payload_hash, out_b["event"].payload_hash)
        self.assertNotEqual(out_a["event"].content_hash, out_b["event"].content_hash)
