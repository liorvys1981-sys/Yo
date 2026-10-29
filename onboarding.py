"""YO CLONE — FASE 2/3/6: incorporacion, captura, calidad, consentimiento, privacidad.

Consentimiento EXPLICITO antes de cualquier captura. Calidad evaluable de forma
determinista (brillo/contraste/varianza del fixture de imagen). 5-10 fotos
recomendadas; solicita mas si la fidelidad no alcanza umbral. Cancelar/repetir/
eliminar siempre permitidos. NADA se transmite a proveedores sin autorizacion
independiente (R1). Datos biométricos reales NUNCA en tests: fixtures sinteticos.
"""
from __future__ import annotations
import hashlib, json, sys, time
from dataclasses import dataclass, field

sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
sys.path.insert(0, "/mnt/agents/output/EL_YO/17_SOVEREIGNTY")
sys.path.insert(0, "/mnt/agents/output/EL_YO/14_DIGITAL_SELF")
from el_yo.evidence import EvidenceLedger
from authority import ChangeAuthorization, verify_authorization, InvalidAuthorization

MIN_PHOTOS = 5
MAX_PHOTOS = 10
FIDELITY_THRESHOLD = 0.6
SENSITIVE_KINDS = ("IMAGE", "VOICE", "VIDEO")


class OnboardingError(Exception):
    code = "ONBOARDING_ERROR"


class ConsentRequired(OnboardingError):
    code = "CONSENT_REQUIRED"


class ProviderTransferUnauthorized(OnboardingError):
    code = "PROVIDER_TRANSFER_UNAUTHORIZED"


def _canon(o): return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


def image_quality_score(fixture: bytes) -> dict:
    """Metricas deterministas de una captura (sintetica en tests; bytes reales en prod).
    Devuelve score 0-1 y razones de rechazo. Sin modelos de vision externos."""
    if len(fixture) < 64:
        return {"score": 0.0, "ok": False, "reasons": ["captura_vacia_o_corrupta"]}
    n = len(fixture)
    mean = sum(fixture[: min(n, 4096)]) / min(n, 4096)
    var = sum((b - mean) ** 2 for b in fixture[: min(n, 4096)]) / min(n, 4096)
    brightness_ok = 40 <= mean <= 215
    contrast = var ** 0.5
    contrast_ok = contrast >= 12
    score = round(min(1.0, 0.5 * (1 if brightness_ok else 0.3) + 0.5 * min(1.0, contrast / 60)), 3)
    reasons = []
    if not brightness_ok: reasons.append("iluminacion_inadecuada")
    if not contrast_ok: reasons.append("contraste_insuficiente")
    return {"score": score, "ok": score >= 0.45, "reasons": reasons}


@dataclass
class ConsentToken:
    token_id: str
    granted: bool
    scopes: tuple            # subset de SENSITIVE_KINDS
    granted_at: float
    revocable: bool = True
    content_hash: str = field(init=False)

    def __post_init__(self):
        payload = {"token_id": self.token_id, "granted": self.granted,
                   "scopes": list(self.scopes), "granted_at": self.granted_at}
        self.content_hash = hashlib.sha256(_canon(payload)).hexdigest()


class OnboardingEngine:
    """Flujo completo: explicar -> consentir -> capturar -> evaluar -> progreso."""

    def __init__(self, user_id: str, tenant: str, ledger: EvidenceLedger | None = None,
                 clock=None):
        self.user_id = user_id
        self.tenant = tenant
        self.ledger = ledger
        self.clock = clock or (lambda: time.time())
        self.consent: ConsentToken | None = None
        self.captures: list[dict] = []
        self.provider_transfers: list[dict] = []

    def _audit(self, event, **kw):
        if self.ledger:
            self.ledger.append({"type": "yoclone", "event": event, "user": self.user_id,
                                "tenant": self.tenant, "ts": self.clock(), **kw})

    def explanation_text(self) -> str:
        return ("Con tu consentimiento explicito, crearas un clon digital tuyo dentro de YO. "
                "Se usaran tus fotos, y opcionalmente voz y video, SOLO para generar tu representacion. "
                "Puedes cancelar, repetir y eliminar todo en cualquier momento. "
                "Nada se envia a proveedores externos sin una autorizacion aparte.")

    def grant_consent(self, scopes: tuple[str, ...]) -> ConsentToken:
        if not scopes or any(s not in SENSITIVE_KINDS for s in scopes):
            raise OnboardingError(f"scopes invalidos: {scopes}")
        self.consent = ConsentToken(token_id=f"consent:{self.user_id}:{self.clock()}",
                                    granted=True, scopes=tuple(scopes),
                                    granted_at=self.clock())
        self._audit("consent_granted", scopes=list(scopes))
        return self.consent

    def _require_consent(self, kind: str):
        if self.consent is None or not self.consent.granted or kind not in self.consent.scopes:
            raise ConsentRequired(f"se requiere consentimiento explicito para {kind}")

    def add_capture(self, kind: str, fixture: bytes, source: str = "camera") -> dict:
        """kind: IMAGE | VOICE | VIDEO. Evalua calidad (IMAGE) y registra con provenance."""
        self._require_consent(kind)
        if kind == "IMAGE":
            images = [c for c in self.captures if c["kind"] == "IMAGE"]
            if len(images) >= MAX_PHOTOS:
                raise OnboardingError("maximo de fotos alcanzado")
            q = image_quality_score(fixture)
            cap = {"kind": kind, "source": source, "sha256": hashlib.sha256(fixture).hexdigest(),
                   "quality": q, "ts": self.clock(), "provenance": "USER_PROVIDED"}
            self.captures.append(cap)
            self._audit("capture", kind=kind, quality=q["score"], ok=q["ok"])
            return cap
        cap = {"kind": kind, "source": source, "sha256": hashlib.sha256(fixture).hexdigest(),
               "quality": {"score": 1.0, "ok": True, "reasons": []}, "ts": self.clock(),
               "provenance": "USER_PROVIDED"}
        self.captures.append(cap)
        self._audit("capture", kind=kind)
        return cap

    def remove_capture(self, sha256_value: str):
        before = len(self.captures)
        self.captures = [c for c in self.captures if c["sha256"] != sha256_value]
        if len(self.captures) == before:
            raise OnboardingError("captura no encontrada")
        self._audit("capture_removed", sha=sha256_value[:16])

    def cancel(self):
        self.captures = []
        self._audit("onboarding_cancelled")

    def progress(self) -> dict:
        images = [c for c in self.captures if c["kind"] == "IMAGE"]
        ok_images = [c for c in images if c["quality"]["ok"]]
        fidelity = round(sum(c["quality"]["score"] for c in ok_images) / max(1, len(ok_images)), 3) if ok_images else 0.0
        return {"photos": len(images), "photos_ok": len(ok_images),
                "recommended": f"{MIN_PHOTOS}-{MAX_PHOTOS}",
                "fidelity": fidelity, "ready": len(ok_images) >= MIN_PHOTOS and fidelity >= FIDELITY_THRESHOLD,
                "needs_more": len(ok_images) < MIN_PHOTOS or fidelity < FIDELITY_THRESHOLD,
                "suggestion": ("solicitar capturas adicionales o grabacion guiada"
                               if (len(ok_images) < MIN_PHOTOS or fidelity < FIDELITY_THRESHOLD)
                               and len(images) >= MAX_PHOTOS else
                               "capturar mas fotos desde distintos angulos")}

    # ---- FASE 6: transferencia a proveedores = autorizacion INDEPENDIENTE (R1) ----
    def authorize_provider_transfer(self, provider: str, data_kinds: tuple,
                                    authorization: ChangeAuthorization | None,
                                    authority_did: str, today: str):
        self._require_consent_for_transfer(data_kinds)
        if authorization is None:
            raise ProviderTransferUnauthorized("transferencia a proveedor exige autorizacion R1")
        content = {"provider": provider, "kinds": list(data_kinds), "user": self.user_id}
        try:
            verify_authorization(authorization, authority_did, "clone-provider-transfer",
                                 today, expected_content_hash=hashlib.sha256(_canon(content)).hexdigest())
        except InvalidAuthorization as e:
            raise ProviderTransferUnauthorized(str(e))
        record = {"provider": provider, "kinds": list(data_kinds), "ts": self.clock(),
                  "authorized": True}
        self.provider_transfers.append(record)
        self._audit("provider_transfer_authorized", provider=provider)
        return record

    def _require_consent_for_transfer(self, data_kinds):
        for k in data_kinds:
            self._require_consent(k)

    def delete_all(self):
        """Eliminacion completa de capturas y datos derivados (politica)."""
        n = len(self.captures)
        self.captures = []
        self.provider_transfers = []
        self._audit("all_data_deleted", removed=n)
        return {"removed": n}
