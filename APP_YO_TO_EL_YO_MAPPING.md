# MAPPING — APP YO consume EL_YO/SAOS17 (no reinventa)

| APP YO necesita | Usa de EL_YO/SAOS17 | NO construye |
|---|---|---|
| Memory (5 tipos) | SOVEREIGN: grafo+vector + provenance | su propia base vectorial |
| Safety Agent enforcement | Autonomic Kernel (mediación) + AuthorizationGate (frase-canal, doble llave) | su propio sistema de permisos paralelo |
| Scheduler | Division Swarm (routing determinista) + scheduler del kernel | cron propio |
| State / Replay | Division Swarm FSM durable + replay | su propio state store |
| Audit / Evidence | evidence_ledger (hash chain) + SAOS17 audit | su propio log |
| Recovery | SAOS17 Recovery + Division Swarm crash recovery | su propio mecanismo |
| Observability | SAOS17 telemetry + OpenFang runtime events | su propio observability stack |
| Identidad criptográfica | identity_engine (DID did:key, VC, revocación) | su propia PKI |
| Evolución con gates | SAOS17 20 gates + Software Factory pattern (worktree isolation) | evolución sin gates |
| Frontera de eventos | webhook_gateway (HMAC, anti-replay) | endpoints crudos |

## Regla de mapeo

Si una capacidad existe en EL_YO/SAOS17, APP YO la consume por COGNITIVE API. Si NO existe y es necesaria para el gemelo → propuesta por Evolution Engine (con justificación GEMELO). Si no es necesaria → NO ENTRA.

## Capacidades nuevas propias de APP YO (las únicas que construye)

Reflection Engine, Pattern extraction, Digital Self models, Evolution Engine (orquestador del pipeline), INTERACTION layer, insight classifier. Todo lo demás es consumo.
