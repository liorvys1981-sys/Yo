# COGNITIVE API — Contrato entre APP YO y EL_YO Control Plane

## Regla de acoplamiento

APP YO solo habla esta API. La API traduce a capacidades de EL_YO/SAOS17. Ningún módulo de APP YO toca infraestructura directamente.

## Recursos y operaciones

| Recurso | Operaciones | Delegación | Política |
|---|---|---|---|
| identity | get / propose_update / approve_update | identity_engine (DID/VC), genome validator | update fundamental = humano + doble llave |
| memory | store / query(scope) / forget | SOVEREIGN + AuthorizationGate | toda query pasa authorization_scope |
| experience | record / get / replay | evidence_ledger + Division Swarm replay | append-only |
| reflection | request / get | Reflection Agent (swarm) bajo policy | agente nivel AGENTE_CON_REGISTRO |
| insights | list / get / state_change | Pattern Agent + genome | INSIGHT→hipótesis; nunca verdad automática |
| goals | create / update_state / close | Division Swarm FSM | transiciones deterministas |
| agents | spawn / status / revoke | OpenFang runtime + capability manifest | sin exceder permisos del manifest |
| capabilities | grant / revoke / check | Autonomic Kernel + AuthorizationGate | probabilístico ≠ autorización |
| policy | get / propose_change | SAOS17 + constitución | cambio = frase-canal |
| evidence | append / verify / anchor | evidence_ledger | verify público dentro del tenant |
| evolution | propose / review / approve / revert | Evolution Engine + gates | pipeline §EVOLUTION_ENGINE_SPEC |
| audit | report / export | SAOS17 audit + ledger | export firmado por DID del gemelo |

## Errores canónicos

`DENIED_POLICY` (gate), `DENIED_TENANT` (scope), `UNPROVENANCED` (genome), `EVOLUTION_LOCKED` (identidad fundamental sin aprobación), `REPLAY_STALE`.

## Multi-tenancy (en todo request)

`{tenant_id, subject_id, cognitive_instance_id, memory_scope, authorization_scope}` — ausencia de cualquiera = DENIED_TENANT.

## Versionado de contrato

v0.1 (diseño). Toda implementación que consuma esta API fija la versión; breaking changes exigen gate de evolución del propio contrato.
