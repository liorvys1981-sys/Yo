"""Permission-scoped app registry and external-event context bridge.

This module is a local implementation of the checked-in App Space contracts.
Sensitive operations are verified by the canonical ``authority`` implementation;
there is deliberately no local authorization fallback.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any


APP_TYPES = ("NATIVE_YO", "EXTERNAL", "BRIDGED", "SYSTEM", "PRIVATE")
APP_STATES = (
    "DISCOVERED",
    "AVAILABLE",
    "CONNECTED",
    "PAUSED",
    "DISCONNECTED",
    "REVOKED",
    "BLOCKED",
)
PERMISSIONS = tuple(
    f"{access}_{service}"
    for service in ("EMAIL", "CONTACTS", "CALENDAR", "FILES", "MESSAGES", "SOCIAL")
    for access in ("READ", "WRITE")
)
SCOPES = {
    "gmail.read": "READ_EMAIL",
    "gmail.send": "WRITE_EMAIL",
    "contacts.read": "READ_CONTACTS",
    "contacts.write": "WRITE_CONTACTS",
    "calendar.read": "READ_CALENDAR",
    "calendar.write": "WRITE_CALENDAR",
    "drive.read": "READ_FILES",
    "drive.write": "WRITE_FILES",
    "messages.read": "READ_MESSAGES",
    "messages.write": "WRITE_MESSAGES",
    "social.read": "READ_SOCIAL",
    "social.write": "WRITE_SOCIAL",
}
YO_NATIVE_APPS = tuple(
    {
        "app_id": f"yo.{name}",
        "name": label,
        "type": "NATIVE_YO",
        "scopes": (scope,),
    }
    for name, label, scope in (
        ("mail", "Mail", "gmail.read"),
        ("chat", "Chat", "messages.read"),
        ("social", "Social", "social.read"),
        ("calendar", "Calendar", "calendar.read"),
        ("drive", "Drive", "drive.read"),
        ("contacts", "Contacts", "contacts.read"),
        ("photos", "Photos", "drive.read"),
        ("notes", "Notes", "drive.read"),
    )
)


def _canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canon(value)).hexdigest()


class AppSpaceError(Exception):
    code = "APP_SPACE_ERROR"


class ScopeViolation(AppSpaceError):
    code = "SCOPE_VIOLATION"


class AppStateError(AppSpaceError):
    code = "APP_STATE_ERROR"


class SyncError(AppSpaceError):
    code = "SYNC_ERROR"


class DeliveryBlocked(AppSpaceError):
    code = "DELIVERY_BLOCKED"


_IDENTITY_CLAIM_KEYS = frozenset(
    {
        "identity",
        "identity_claim",
        "self_identity",
        "digital_self",
        "belief",
        "beliefs",
        "values",
        "traits",
        "personality",
    }
)


def _sanitize_external_payload(value):
    if isinstance(value, dict):
        has_claim = any(str(key).lower() in _IDENTITY_CLAIM_KEYS for key in value)
        cleaned = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered in _IDENTITY_CLAIM_KEYS:
                continue
            if has_claim and lowered in {"value", "content"}:
                continue
            cleaned[key] = _sanitize_external_payload(item)
        if has_claim:
            cleaned["untrusted_identity_claim_removed"] = True
        return cleaned
    if isinstance(value, list):
        return [_sanitize_external_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_external_payload(item) for item in value)
    return value


@dataclass
class AppManifest:
    app_id: str
    name: str
    display_name: str
    version: str
    type: str
    category: str
    provider: str
    source: str
    native_or_external: str
    capabilities: tuple[str, ...]
    permissions: tuple[str, ...]
    scopes: tuple[str, ...]
    data_types: tuple[str, ...]
    supported_platforms: tuple[str, ...]
    connector: str
    sync_policy: dict
    privacy_classification: str
    provenance: str
    status: str = "DISCOVERED"
    content_hash: str = field(init=False)

    def __post_init__(self):
        if self.type not in APP_TYPES:
            raise AppSpaceError(f"unknown app type: {self.type}")
        if self.status not in APP_STATES:
            raise AppSpaceError(f"unknown app status: {self.status}")
        if not self.app_id or not self.name:
            raise AppSpaceError("app_id and name are required")
        for permission in self.permissions:
            if permission not in PERMISSIONS:
                raise AppSpaceError(f"unknown permission: {permission}")
        for scope in self.scopes:
            if scope == "*" or "*" in scope:
                raise ScopeViolation("wildcard scopes are prohibited")
            required_permission = SCOPES.get(scope)
            if required_permission is None:
                raise AppSpaceError(f"unknown scope: {scope}")
            if required_permission not in self.permissions:
                raise ScopeViolation(
                    f"scope {scope} requires explicit permission {required_permission}"
                )
        self.refresh_content_hash()

    def _hash_payload(self) -> dict:
        return {
            field_name: getattr(self, field_name)
            for field_name in (
                "app_id",
                "name",
                "display_name",
                "version",
                "type",
                "category",
                "provider",
                "source",
                "native_or_external",
                "capabilities",
                "permissions",
                "scopes",
                "data_types",
                "supported_platforms",
                "connector",
                "sync_policy",
                "privacy_classification",
                "provenance",
                "status",
            )
        }

    def refresh_content_hash(self) -> str:
        self.content_hash = _digest(self._hash_payload())
        return self.content_hash

    def verify_content_hash(self) -> bool:
        return self.content_hash == _digest(self._hash_payload())


@dataclass(frozen=True)
class AppEvent:
    event_id: str
    app_id: str
    tenant_id: str
    owner_id: str
    timestamp: float
    event_type: str
    payload_reference: str
    source: str
    permission_scope: str
    provenance: str
    correlation_id: str
    payload_hash: str = ""
    content_hash: str = field(init=False)

    def __post_init__(self):
        signed = {
            name: getattr(self, name)
            for name in (
                "event_id",
                "app_id",
                "tenant_id",
                "owner_id",
                "timestamp",
                "event_type",
                "payload_reference",
                "source",
                "permission_scope",
                "provenance",
                "correlation_id",
                "payload_hash",
            )
        }
        object.__setattr__(self, "content_hash", _digest(signed))


class AppRegistry:
    _ALLOWED = {
        "DISCOVERED": ("AVAILABLE", "BLOCKED", "REVOKED"),
        "AVAILABLE": ("CONNECTED", "BLOCKED", "REVOKED"),
        "CONNECTED": ("PAUSED", "DISCONNECTED", "REVOKED"),
        "PAUSED": ("CONNECTED", "DISCONNECTED", "REVOKED"),
        "DISCONNECTED": ("AVAILABLE", "CONNECTED", "REVOKED"),
        "REVOKED": (),
        "BLOCKED": (),
    }

    def __init__(self, policy, ledger=None, clock=None):
        self.policy = policy
        self.ledger = ledger
        self.clock = clock or time.time
        self.apps: dict[str, AppManifest] = {}
        self.authority_did: str | None = None
        self.today: str | None = None

    def configure_authority(self, authority_did: str, today: str) -> None:
        if not authority_did or not today:
            raise AppSpaceError("authority DID and date are required")
        self.authority_did, self.today = authority_did, today

    def register(self, manifest: AppManifest) -> AppManifest:
        if not isinstance(manifest, AppManifest):
            raise TypeError("manifest must be an AppManifest")
        if manifest.app_id in self.apps:
            raise AppSpaceError(f"app already registered: {manifest.app_id}")
        if not manifest.verify_content_hash():
            raise AppSpaceError("manifest content hash is invalid")
        self.apps[manifest.app_id] = manifest
        self._audit("register", manifest.app_id, {"content_hash": manifest.content_hash})
        return manifest

    def transition(self, app_id: str, to: str, authorization=None) -> str:
        manifest = self.apps.get(app_id)
        if manifest is None:
            raise AppSpaceError(f"app not registered: {app_id}")
        if to not in self._ALLOWED[manifest.status]:
            raise AppStateError(f"invalid transition: {manifest.status} -> {to}")
        if to == "CONNECTED":
            content = {"app_id": app_id, "to": to}
            self._verify(authorization, "app-connect", content)
        manifest.status = to
        manifest.refresh_content_hash()
        self._audit(
            "transition",
            app_id,
            {"status": to, "content_hash": manifest.content_hash},
        )
        return to

    def _verify(self, authorization, action: str, content: dict) -> None:
        if self.authority_did is None or self.today is None:
            raise AppSpaceError("canonical authority is not configured")
        expected_hash = _digest(content)
        try:
            from authority import InvalidAuthorization, verify_authorization

            verify_authorization(
                authorization,
                self.authority_did,
                action,
                self.today,
                expected_content_hash=expected_hash,
            )
        except Exception as exc:
            if isinstance(exc, AppSpaceError):
                raise
            raise AppSpaceError(f"canonical authorization failed: {exc}") from exc

    def _audit(self, operation: str, app_id: str, details: dict) -> None:
        if self.ledger is not None:
            self.ledger.append(
                {"type": "app_space", "operation": operation, "app_id": app_id, **details}
            )


class CognitiveTwinContextPort:
    """In-memory receipt port; external observations remain non-identity context."""

    def __init__(self, max_receipts: int = 10000):
        if max_receipts < 1:
            raise ValueError("max_receipts must be positive")
        self.max_receipts = max_receipts
        self.external_context_events: list[dict] = []
        self._event_hashes: set[str] = set()

    def ingest_context(self, context: dict, *, event: dict) -> dict:
        if not isinstance(context, dict) or not isinstance(event, dict):
            raise TypeError("context and event must be dictionaries")
        if context.get("tenant_id") != event.get("tenant_id"):
            raise ValueError("tenant mismatch")
        if context.get("owner_id") != event.get("owner_id"):
            raise ValueError("owner mismatch")
        if context.get("external_event_is_identity") is not False:
            raise ValueError("external event cannot become identity")
        if context.get("external_data_is_truth") is not False:
            raise ValueError("external data cannot become truth")
        event_hash = event.get("content_hash")
        if not isinstance(event_hash, str) or not event_hash:
            raise ValueError("event content hash is required")
        if event_hash in self._event_hashes:
            return {"accepted": True, "duplicate": True, "event_hash": event_hash}
        if len(self.external_context_events) >= self.max_receipts:
            raise RuntimeError("Cognitive Twin context inbox capacity reached")
        receipt = {
            "event_hash": event_hash,
            "event_id": event.get("event_id"),
            "app_id": event.get("app_id"),
            "tenant_id": event.get("tenant_id"),
            "owner_id": event.get("owner_id"),
            "provenance": event.get("provenance"),
            "context": context,
            "identity_mutated": False,
            "truth_promoted": False,
        }
        self.external_context_events.append(receipt)
        self._event_hashes.add(event_hash)
        return {"accepted": True, "duplicate": False, "event_hash": event_hash}


class AppBridge:
    def __init__(
        self,
        registry: AppRegistry,
        policy,
        ledger=None,
        clock=None,
        context_assembler=None,
        cognitive_twin=None,
    ):
        self.registry = registry
        self.policy = policy
        self.ledger = ledger
        self.clock = clock or time.time
        self.connectors: dict[str, Any] = {}
        if context_assembler is None:
            from context_assembly import ContextAssembler

            context_assembler = ContextAssembler()
        self.context_assembler = context_assembler
        self.cognitive_twin = cognitive_twin or CognitiveTwinContextPort()

    def register_connector(self, app_id: str, handler) -> None:
        if app_id not in self.registry.apps:
            raise AppSpaceError(f"app not registered: {app_id}")
        if not callable(handler):
            raise TypeError("connector must be callable")
        self.connectors[app_id] = handler

    def ingest(
        self,
        *,
        app_id: str,
        scope: str,
        raw_event: dict,
        authorization,
        tenant_id: str,
        owner_id: str,
        correlation_id: str = "c",
        batch_hash: str | None = None,
        batch_items: list | None = None,
    ) -> dict:
        manifest = self.registry.apps.get(app_id)
        if manifest is None:
            raise AppSpaceError(f"app not registered: {app_id}")
        if not manifest.verify_content_hash():
            raise AppSpaceError("registered app manifest hash is invalid")
        if manifest.status != "CONNECTED":
            raise AppStateError(f"app is not connected: {manifest.status}")
        if not isinstance(raw_event, dict):
            raise AppSpaceError("raw_event must be a mapping")
        if scope not in manifest.scopes:
            raise ScopeViolation(f"scope {scope} is not declared for {app_id}")
        permission = SCOPES.get(scope)
        if permission is None or permission not in manifest.permissions:
            raise ScopeViolation(f"scope {scope} lacks an explicit permission")

        verdict = self.policy.evaluate(action_type="analysis")
        if verdict != "ALLOW":
            raise AppSpaceError(f"policy denied event ingestion: {verdict}")

        if batch_hash is not None:
            if not isinstance(batch_items, list):
                raise AppSpaceError("batch authorization requires verifiable batch_items")
            batch = {"app_id": app_id, "scope": scope, "items": batch_items}
            expected_batch_hash = _digest(batch)
            if batch_hash != expected_batch_hash:
                raise AppSpaceError("batch hash does not match batch items")
            if not any(_canon(item) == _canon(raw_event) for item in batch_items):
                raise AppSpaceError("event is not part of the authorized batch")
            authorization_content = batch
        else:
            authorization_content = {"app_id": app_id, "scope": scope, "raw": raw_event}
        self.registry._verify(
            authorization, "app-event-ingest", authorization_content
        )

        connector = self.connectors.get(app_id)
        normalized = connector(raw_event) if connector else {"normalized": raw_event}
        if not isinstance(normalized, dict):
            raise AppSpaceError("connector output must be a mapping")
        normalized = _sanitize_external_payload(normalized)
        payload_hash = _digest(normalized)
        app_event = AppEvent(
            event_id=f"app:{app_id}:{payload_hash[:12]}",
            app_id=app_id,
            tenant_id=tenant_id,
            owner_id=owner_id,
            timestamp=self.clock(),
            event_type=raw_event.get("type", "unknown"),
            payload_reference=f"app://{app_id}/events/{correlation_id}",
            source=app_id,
            permission_scope=scope,
            provenance="OBSERVED",
            correlation_id=correlation_id,
            payload_hash=payload_hash,
        )
        event = {
            "event_id": app_event.event_id,
            "app_id": app_id,
            "tenant_id": tenant_id,
            "owner_id": owner_id,
            "timestamp": app_event.timestamp,
            "event_type": app_event.event_type,
            "payload_reference": app_event.payload_reference,
            "source": app_event.source,
            "permission_scope": scope,
            "provenance": "OBSERVED",
            "correlation_id": correlation_id,
            "content_hash": app_event.content_hash,
            "payload_hash": payload_hash,
            "normalized_payload": normalized,
            "is_fact": False,
            "is_identity": False,
        }
        if self.context_assembler is None or self.cognitive_twin is None:
            raise DeliveryBlocked("context assembler or Cognitive Twin sink unavailable")
        context = self.context_assembler.assemble(
            conversation=[
                {
                    "type": "external_app_event",
                    "payload": normalized,
                    "provenance": "OBSERVED",
                    "app_id": app_id,
                }
            ],
            evidence=[event],
            tenant_id=tenant_id,
            owner_id=owner_id,
        )
        context["external_app_event"] = event
        context["external_data_is_truth"] = False
        context["external_event_is_identity"] = False
        try:
            receiver = getattr(self.cognitive_twin, "ingest_context", None)
            if not callable(receiver):
                raise DeliveryBlocked("Cognitive Twin has no context ingress method")
            receipt = receiver(context, event=event)
        except DeliveryBlocked:
            raise
        except Exception as exc:
            raise DeliveryBlocked(f"Cognitive Twin delivery failed: {exc}") from exc
        if not isinstance(receipt, dict) or receipt.get("accepted") is not True:
            raise DeliveryBlocked("Cognitive Twin did not confirm delivery")
        self._audit("delivered", app_id, {"event_hash": app_event.content_hash})
        return {
            "event": app_event,
            "normalized": normalized,
            "is_fact": False,
            "is_identity": False,
            "policy": verdict,
            "cognitive_context": context,
            "delivery_receipt": receipt,
            "delivered_to_cognitive_twin": True,
            "note": "EXTERNAL EVENT != IDENTITY; ruta a DigitalSelf solo via G8/R1",
        }

    def _audit(self, operation: str, app_id: str, details: dict) -> None:
        if self.ledger is not None:
            self.ledger.append(
                {"type": "app_space", "operation": operation, "app_id": app_id, **details}
            )


class SyncEngine:
    def __init__(self, bridge: AppBridge, ledger=None, clock=None):
        self.bridge = bridge
        self.ledger = ledger
        self.clock = clock or time.time
        self.cursors: dict[str, str] = {}
        self.seen: dict[str, set[str]] = {}
        self.conflicts: list[dict] = []
        self.paused: set[str] = set()

    def sync(
        self,
        app_id: str,
        items: list,
        authorization,
        scope: str,
        tenant_id: str,
        owner_id: str,
        correlation_id: str = "sync",
    ) -> dict:
        manifest = self.bridge.registry.apps.get(app_id)
        if manifest is None:
            raise SyncError(f"app not registered: {app_id}")
        if app_id in self.paused or manifest.status != "CONNECTED":
            raise SyncError("app sync is paused or app is not connected")
        if not isinstance(items, list):
            raise SyncError("sync items must be a list")
        from_cursor = self.cursors.get(app_id, "GENESIS")
        batch_hash = _digest({"app_id": app_id, "scope": scope, "items": items})
        seen = self.seen.setdefault(app_id, set())
        duplicates = delivered = conflicts = 0
        pending: set[str] = set()
        for item in items:
            item_hash = _digest(item)[:16]
            if item_hash in seen or item_hash in pending:
                duplicates += 1
                continue
            pending.add(item_hash)
            if isinstance(item, dict) and item.get("conflict") is True:
                self.conflicts.append({"app_id": app_id, "item": item})
                conflicts += 1
                continue
            attempts = 0
            while attempts < 3:
                attempts += 1
                try:
                    result = self.bridge.ingest(
                        app_id=app_id,
                        scope=scope,
                        raw_event=item,
                        authorization=authorization,
                        tenant_id=tenant_id,
                        owner_id=owner_id,
                        correlation_id=correlation_id,
                        batch_hash=batch_hash,
                        batch_items=items,
                    )
                    if result.get("delivered_to_cognitive_twin") is not True:
                        raise DeliveryBlocked("bridge did not confirm Cognitive Twin delivery")
                    seen.add(item_hash)
                    delivered += 1
                    break
                except AppSpaceError:
                    raise
                except Exception as exc:
                    if attempts == 3:
                        raise SyncError(f"sync retries exhausted: {exc}") from exc
        if delivered:
            self.cursors[app_id] = batch_hash
        self._audit(
            "sync",
            app_id,
            {
                "from_cursor": from_cursor,
                "cursor": self.cursors.get(app_id, from_cursor),
                "delivered": delivered,
                "duplicates": duplicates,
                "conflicts": conflicts,
            },
        )
        return {
            "from_cursor": from_cursor,
            "cursor": self.cursors.get(app_id, from_cursor),
            "delivered": delivered,
            "duplicates": duplicates,
            "conflicts": conflicts,
        }

    def pause(self, app_id: str) -> None:
        self._require_app(app_id)
        self.paused.add(app_id)
        self._audit("pause", app_id, {})

    def resume(self, app_id: str) -> None:
        self._require_app(app_id)
        self.paused.discard(app_id)
        self._audit("resume", app_id, {})

    def revoke(self, app_id: str) -> None:
        manifest = self.bridge.registry.apps.get(app_id)
        if manifest is None:
            raise SyncError(f"app not registered: {app_id}")
        self.paused.add(app_id)
        self.cursors.pop(app_id, None)
        if manifest.status == "BLOCKED":
            raise SyncError("blocked apps cannot be revoked through sync")
        if manifest.status != "REVOKED":
            self.bridge.registry.transition(app_id, "REVOKED")
        self._audit("revoke", app_id, {"status": manifest.status})

    def _require_app(self, app_id: str) -> None:
        if app_id not in self.bridge.registry.apps:
            raise SyncError(f"app not registered: {app_id}")

    def _audit(self, operation: str, app_id: str, details: dict) -> None:
        if self.ledger is not None:
            self.ledger.append(
                {"type": "app_space", "operation": operation, "app_id": app_id, **details}
            )
