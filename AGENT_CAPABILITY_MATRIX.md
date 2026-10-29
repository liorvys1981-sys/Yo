# COGNITIVE SWARM — Matriz de Capacidades por Agente

## Reglas comunes (todos)

identidad (DID propia delegada), propósito, capacidades explícitas, permisos, límites, memoria permitida (scope), herramientas permitidas, política, evidencia obligatoria, estado, recuperación.
**Ningún agente salta el Policy/Capability Gateway. El Safety Agent puede bloquear a cualquiera, incluido a sí mismo vía segundo factor.**

## Matriz

| Agente | Propósito | Capacidades | Límites | Memoria permitida | Herramientas | Nivel gate |
|---|---|---|---|---|---|---|
| Identity Agent | mantener coherencia del genoma de identidad | proponer cambios de identidad, detectar contradicciones | NO aplica cambios fundamentales sin aprobación humana | IDENTITY scope | genome validator | AGENTE_CON_REGISTRO (propuestas) / HUMANO_DOBLE_LLAVE (aplicación) |
| Memory Agent | curaduría de memorias | consolidar episódicas→semánticas, marcar procedencia, resolver conflictos de fuente | no borra sin propuesta + evidencia; no fusiona tenants | MEMORY scope | SOVEREIGN API | AGENTE_CON_REGISTRO |
| Reflection Agent | generar reflexiones | sintetizar experiencias→reflexiones, proponer hipótesis | toda salida etiquetada INFERRED/UNCERTAIN | EXPERIENCE+MEMORY read | LLM local (OpenFang runtime) | AGENTE_CON_REGISTRO |
| Pattern Agent | detectar patrones | correlacionar eventos, producir PATTERN/HYPOTHESIS | hipótesis ≠ verdad; confianza obligatoria | EXPERIENCE+INSIGHTS | memoria query (autorizada) | AGENTE_CON_REGISTRO |
| Future Agent | proyecciones | construir YO Futuro / YO Potencial como escenarios versionados | proyecciones NO hechos; nunca escriben EXPERIENCE | INSIGHTS read | modelos de escenario | AGENTE_AUTONOMO (solo construcción) |
| Safety Agent | protección | veto sobre cualquier acción, auditoría de intents, degradación de autonomía | sus vetos requieren evidencia; inamovible por otros agentes | SECURITY+POLICY read | policy engine | HUMANO_DOBLE_LLAVE para cambiar sus reglas |

## Trust ramp (adaptado de AOS, ADAPTAR)

Cada agente inicia en nivel **shadow** (propone, no ejecuta). Promoción a approval → autonomous por evidencia acumulada en evidence_ledger (N ejecuciones correctas auditadas). Degradación automática ante incidente.
