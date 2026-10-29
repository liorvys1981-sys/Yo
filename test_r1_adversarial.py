"""R1 ADVERSARIAL — demostrar que ningun caller no autorizado modifica el DigitalSelf."""
import os, sys, tempfile, unittest
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from digital_self import DigitalSelf
from genome_store import GenomeStore
from authority import Authority, ChangeAuthorization, verify_authorization, InvalidAuthorization
from identity import Identity
from el_yo.constitution import Denied
from el_yo.gates import AuthorizationGate, DailyCodeProvider

KEY = b"g" * 32
TODAY = "2026-10-07"
AUTH = Identity(seed=b"a" * 32)          # autoridad (clave privada en control plane)
GATE = AuthorizationGate(DailyCodeProvider(KEY), TODAY, second_key_present=True)
CODE = DailyCodeProvider(KEY).code(TODAY)


def mk_ds():
    ds = DigitalSelf("s", "t")
    for k in ("Identity", "Values", "Beliefs", "Goals", "Traits", "Relationships", "Experiences"):
        ds.create(k)
    return ds


def mk_store():
    tmp = tempfile.mkdtemp()
    return tmp, GenomeStore(tmp, os.path.join(tmp, "ledger.jsonl"),
                            authority_did=AUTH.did, today=TODAY)


class TestFundamentalesSinAutorizacion(unittest.TestCase):
    def test_identity_directo_denied(self):
        _, st = mk_store()
        ds = mk_ds()
        with self.assertRaises(Denied):
            st.change(ds, "Identity", {"n": "x"}, "SELF_REPORTED", 1.0, ("e",), "s", "bypass")

    def test_values_directo_denied(self):
        _, st = mk_store()
        ds = mk_ds()
        with self.assertRaises(Denied):
            st.change(ds, "Values", {"v": "x"}, "SELF_REPORTED", 1.0, ("e",), "s", "bypass")

    def test_beliefs_directo_denied(self):
        _, st = mk_store()
        ds = mk_ds()
        with self.assertRaises(Denied):
            st.change(ds, "Beliefs", {"b": "x"}, "SELF_REPORTED", 1.0, ("e",), "s", "bypass")


class TestApprovedByFalsificadoImposible(unittest.TestCase):
    """R1: ya no existe parametro approved_by libre en la ruta de fundamentales."""
    def test_firma_falsificada_rechazada(self):
        _, st = mk_store()
        ds = mk_ds()
        fake = Identity(seed=b"f" * 32)
        payload = {"kind": "Identity", "did": fake.did, "day": TODAY, "nonce": "0123456789abcdef"}
        import json as J
        authz = ChangeAuthorization("Identity", fake.did, TODAY, "0123456789abcdef",
                                    fake.sign(J.dumps(payload, sort_keys=True, separators=(",", ":")).encode()))
        with self.assertRaises(Denied):     # DID no es la autoridad configurada
            st.change(ds, "Identity", {"n": "x"}, "SELF_REPORTED", 1.0, ("e",), "s", "bypass",
                      authorization=authz)

    def test_firma_valida_otro_dia_rechazada(self):
        _, st = mk_store()                          # store con today=2026-10-07
        ds = mk_ds()
        # autoridad bajo gate del DIA X emite correctamente...
        gate_06 = AuthorizationGate(DailyCodeProvider(KEY), "2026-10-06", second_key_present=True)
        a06 = Authority(AUTH, gate_06, "2026-10-06")
        code_06 = DailyCodeProvider(KEY).code("2026-10-06")
        authz = a06.authorize_change("Values", f"EJECUTA frescura {code_06}")
        self.assertEqual(authz.day, "2026-10-06")   # emitida bajo gate real del dia X
        with self.assertRaises(Denied):             # ...pero el store (day=Y) la rechaza
            st.change(ds, "Values", {"v": 1}, "SELF_REPORTED", 1.0, ("e",), "s", "bypass",
                      authorization=authz)

    def test_kind_vinculado_distinto_rechazado(self):
        _, st = mk_store()
        ds = mk_ds()
        a = Authority(AUTH, GATE, TODAY)
        authz = a.authorize_change("Beliefs", f"EJECUTA vinculo {CODE}")
        with self.assertRaises(Denied):             # autorizacion para Beliefs usada en Values
            st.change(ds, "Values", {"v": 1}, "SELF_REPORTED", 1.0, ("e",), "s", "bypass",
                      authorization=authz)

    def test_objeto_arbitrario_rechazado(self):
        _, st = mk_store()
        ds = mk_ds()
        with self.assertRaises(Denied):
            st.change(ds, "Beliefs", {"b": 1}, "SELF_REPORTED", 1.0, ("e",), "s", "x",
                      authorization="approved_by=fake-user")

    def test_verify_rechaza_none_y_vacio(self):
        for bad in (None, "", "admin"):
            with self.assertRaises(InvalidAuthorization):
                verify_authorization(bad, AUTH.did, "Identity", TODAY)


class TestRutaLegitimaFunciona(unittest.TestCase):
    def test_authority_emite_tras_gate_y_store_acepta(self):
        _, st = mk_store()
        ds = mk_ds()
        a = Authority(AUTH, GATE, TODAY)
        authz = a.authorize_change("Beliefs", f"EJECUTA genesis {CODE}")
        ev = st.change(ds, "Beliefs", {"b": "declarada"}, "SELF_REPORTED", 1.0,
                       ("e",), "s", "declaracion", authorization=authz)
        self.assertEqual(ds.get("Beliefs").active.content, {"b": "declarada"})
        self.assertEqual(ev["version"], 1)

    def test_aprobador_registrado_es_did_verificable(self):
        _, st = mk_store()
        ds = mk_ds()
        a = Authority(AUTH, GATE, TODAY)
        authz = a.authorize_change("Identity", f"EJECUTA genesis {CODE}")
        st.change(ds, "Identity", {"n": "yo"}, "SELF_REPORTED", 1.0, ("e",), "s", "genesis",
                  authorization=authz)
        self.assertEqual(ds.get("Identity").active.approved_by, AUTH.did)
        self.assertTrue(ds.get("Identity").active.approved_by.startswith("did:key:"))

    def test_authority_sin_frase_valida_no_emite(self):
        a = Authority(AUTH, GATE, TODAY)
        with self.assertRaises(Denied):
            a.authorize_change("Identity", "frase falsa")

    def test_no_fundamental_no_requiere_autorizacion(self):
        _, st = mk_store()
        ds = mk_ds()
        ev = st.change(ds, "Goals", {"g": 1}, "SELF_REPORTED", 0.9, ("e",), "s", "r")
        self.assertEqual(ev["version"], 1)


if __name__ == "__main__":
    unittest.main()
