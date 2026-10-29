"""P10-B9 CONSTRUIR ELLA — produce YO'S MODEL OF ELLA (propuesta, namespace YO).
NUNCA produce ELLA'S IDENTITY. Imagination etiquetada IMAGINED explicitamente."""
from __future__ import annotations
import hashlib, json, sys

sys.path.insert(0, "/mnt/agents/output/APP_YO/onboarding")


class BuildEllaError(Exception):
    code = "BUILD_ELLA_ERROR"


def _canon(o) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


def construir_ella(twin_snapshot: dict, maturity: dict,
                   imagination: dict | None = None,
                   visual_preferences: dict | None = None,
                   memory_refs: tuple = ()) -> dict:
    if not maturity.get("ready_for_ella"):
        raise BuildEllaError(f"CONSTRUIR ELLA bloqueado: {maturity.get('ready_explanation')}")

    def grab(path):
        v = twin_snapshot
        for p in path:
            v = v.get(p, {}) if isinstance(v, dict) else {}
        return v if v else None

    model = {
        "model_id": "yo-model-ella:" + hashlib.sha256(_canon([str(twin_snapshot.get('Memory')),
                                                              maturity["score"]])).hexdigest()[:12],
        "namespace": "YO",
        "kind": "YO'S MODEL OF ELLA",
        "provenance": "INFERRED",
        "provenance_subtype": "YO_MODEL_OF_ELLA",
        "not_ella_identity": True,
        "from_twin": {
            "values": grab(("Values",)) or {"status": "NO EVIDENCE"},
            "experiences": grab(("Experiences",)) or {"status": "NO EVIDENCE"},
            "memory_refs": list(memory_refs),
            "patterns": grab(("Patterns", "items")) or [],
            "insights": [i for i in (grab(("Insights", "items")) or [])
                         if i.get("tag") in ("interpretation", "hypothesis")],
            "purpose": grab(("Purpose",)) or {"status": "NO EVIDENCE"},
        },
        "evidence": {"maturity_score": maturity["score"],
                     "criteria": {k: v["value"] for k, v in maturity["criteria"].items()}},
        "confidence": round(maturity["score"] * 0.9, 3),
    }
    if imagination:
        model["imagination"] = {"content": imagination, "provenance": "IMAGINED",
                                "explicit": True}
    if visual_preferences:
        model["visual_preferences"] = {"content": visual_preferences,
                                       "provenance": "SELF_REPORTED", "explicit": True}
    model["model_hash"] = hashlib.sha256(_canon(model)).hexdigest()
    return model
