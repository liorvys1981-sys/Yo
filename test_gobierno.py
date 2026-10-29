import sys, unittest
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from el_yo.constitution import Action, Denied, required_authorization
from el_yo.gates import AuthorizationGate, DailyCodeProvider
from el_yo.evidence import EvidenceLedger, TamperedError
import importlib.util as _il
_spec = _il.spec_from_file_location('webhook', '/mnt/agents/output/EL_YO/18_SECURITY/webhook.py')
_wh = _il.module_from_spec(_spec); _spec.loader.exec_module(_wh)
WebhookValidator = _wh.WebhookValidator

KEY = b'k' * 32
TODAY = '2026-10-07'


class TestGobiernoPort(unittest.TestCase):
    def test_informativa(self):
        assert required_authorization("informativa") == "AGENTE_AUTONOMO"

    def test_reversible(self):
        assert required_authorization("reversible_menor") == "AGENTE_CON_REGISTRO"

    def test_externa(self):
        assert required_authorization("externa_irreversible") == "HUMANO_CON_FRASE_CANAL"

    def test_destructiva(self):
        assert required_authorization("destructiva") == "HUMANO_DOBLE_LLAVE"

    def test_impacto_desconocido(self):
        with self.assertRaises(ValueError):
            Action(kind="x", impact="inventado")


class TestGates:
    def test_informativa_agente(self):
        g = AuthorizationGate(self.codes, TODAY)
        r = g.authorize(Action("leer", "informativa"), actor="agente")
        assert r["decision"] == "ALLOW" and r["log"] is False

    def test_externa_denegada_a_agente(self):
        g = AuthorizationGate(self.codes, TODAY)
        with self.assertRaises(Denied):
            g.authorize(Action("enviar", "externa_irreversible"), actor="agente")

    def test_externa_humano_ok(self):
        g = AuthorizationGate(self.codes, TODAY)
        r = g.authorize(Action("enviar", "externa_irreversible"), actor="humano",
                        phrase=make_phrase(self.code))
        assert r["decision"] == "ALLOW"

    def test_externa_codigo_erroneo(self):
        g = AuthorizationGate(self.codes, TODAY)
        with self.assertRaises(Denied):
            g.authorize(Action("enviar", "externa_irreversible"), actor="humano",
                        phrase="AUTORIZA pago deadbeefcafe")

    def test_externa_mal_formato(self):
        g = AuthorizationGate(self.codes, TODAY)
        with self.assertRaises(Denied):
            g.authorize(Action("enviar", "externa_irreversible"), actor="humano",
                        phrase="hola")

    def test_destructiva_sin_segunda_llave(self):
        g = AuthorizationGate(self.codes, TODAY, second_key_present=False)
        with self.assertRaises(Denied):
            g.authorize(Action("purgar", "destructiva"), actor="humano",
                        phrase=make_phrase(self.code))

    def test_destructiva_doble_llave_ok(self):
        g = AuthorizationGate(self.codes, TODAY, second_key_present=True)
        r = g.authorize(Action("purgar", "destructiva"), actor="humano",
                        phrase=make_phrase(self.code))
        assert r["decision"] == "ALLOW"

    def test_codigo_cambia_por_dia(self):
        assert self.codes.code("2026-10-07") != self.codes.code("2026-10-08")

    def test_determinismo_codigo(self):
        assert DailyCodeProvider(KEY).code(TODAY) == self.code


class TestEvidence:
    def test_cadena_verifica(self, tmp_path):
        p = str(tmp_path / "ledger.jsonl")
        l = EvidenceLedger(p)
        e1 = l.append({"test": "a"})
        e2 = l.append({"test": "b"})
        assert e2["prev"] == e1["hash"] and l.verify() is True

    def test_tamper_detectado(self, tmp_path):
        p = str(tmp_path / "ledger.jsonl")
        EvidenceLedger(p).append({"test": "a"})
        with open(p) as f:
            lines = f.readlines()
        lines[0] = lines[0].replace('"a"', '"b"')
        with open(p, "w") as f:
            f.writelines(lines)
        with self.assertRaises(TamperedError):
            EvidenceLedger(p).verify()

    def test_hash_depende_de_orden(self, tmp_path):
        p = str(tmp_path / "ledger.jsonl")
        l = EvidenceLedger(p)
        e1 = l.append({"n": 1})
        e2 = l.append({"n": 2})
        assert e1["hash"] != e2["hash"]


class TestWebhook:
    TS = 1_900_000_000

    def test_valido(self):
        v = WebhookValidator(KEY)
        sig = v.sign(self.TS, b"{}", "pagos")
        assert v.validate(b"{}", sig, self.TS, endpoint="pagos", now=self.TS) is True

    def test_firma_invalida(self):
        v = WebhookValidator(KEY)
        assert v.validate(b"{}", "f" * 64, self.TS, endpoint="pagos", now=self.TS) is False

    def test_ts_expirado(self):
        v = WebhookValidator(KEY)
        sig = v.sign(self.TS, b"{}", "pagos")
        assert v.validate(b"{}", sig, self.TS, endpoint="pagos", now=self.TS + 400) is False

    def test_replay_rechazado(self):
        v = WebhookValidator(KEY)
        sig = v.sign(self.TS, b"{}", "pagos")
        assert v.validate(b"{}", sig, self.TS, endpoint="pagos", now=self.TS) is True
        assert v.validate(b"{}", sig, self.TS, endpoint="pagos", now=self.TS + 1) is False

    def test_ip_fuera_allowlist(self):
        v = WebhookValidator(KEY)
        sig = v.sign(self.TS, b"{}", "pagos")
        ok = v.validate(b"{}", sig, self.TS, endpoint="pagos", ip="1.2.3.4",
                        allowlist={"9.9.9.9"}, now=self.TS)
        assert ok is False

    def test_determinismo_100(self):
        # instancias frescas: el anti-replay stateful es comportamiento CORRECTO
        sig = WebhookValidator(KEY).sign(self.TS, b'{"x":1}', "e")
        results = [
            WebhookValidator(KEY).validate(b'{"x":1}', sig, self.TS, endpoint="e", now=self.TS)
            for _ in range(100)
        ]
        assert all(results)
