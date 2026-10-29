# GEMELO COGNITIVO — Especificación del Núcleo Conceptual

## Definición

No es un chatbot. Es la representación progresiva de:
IDENTIDAD + MEMORIA + EXPERIENCIA + REFLEXIÓN + PATRONES + OBJETIVOS + VALORES + APRENDIZAJE + PROYECCIÓN FUTURA + EVOLUCIÓN.

## Equación de estado

```
Gemelo(t) = { Identidad_v(t), Memorias(t), Experiencias_acum(t), Patrones(t),
              Insights(t), Objetivos(t), Valores_v(t), Modelos_YO(t), Evoluciones_v(t) }
```
El gemelo cambia por dos vías: (a) experiencias registradas (OBSERVED), (b) evoluciones versionadas aprobadas (SYSTEM_DERIVED con gate).

## Lo que el gemelo NO es

- No un perfil estático: evoluciona con evidencia.
- No un oráculo: toda afirmación sobre la persona lleva procedencia y confianza.
- No autónomo sin freno: acciones externas requieren frase-canal (Anexo A); destructivas doble llave (Art. 4.2).

## Verificación del gemelo

- Cada afirmación del gemelo es verificable: fuente, fecha, modelo/agente, confianza, versión (evidence_ledger).
- El gemelo puede responder: "qué sabía de mí el 2026-06-01 y bajo qué evidencia".
- Divergencia gemelo-realidad detectable: comparar predicciones (YO Futuro) con resultados (EXPERIENCIA).

## Dependencias de capa inferior

| Capacidad del gemelo | Proveedor |
|---|---|
| persistencia de estado | Division Swarm |
| ejecución de agentes | OpenFang |
| autoridad/seguridad | Autonomic Kernel + AuthorizationGate |
| memoria con procedencia | SOVEREIGN |
| evidencia/auditoría | evidence_ledger (in-house) |
| identidad | identity_engine (in-house, DID/VC) |

## Criterio de madurez

Gemelo v1.0 = cuando el ciclo EXPERIENCIA→...→EVOLUCIÓN corre completo con gates ejecutables y evidencia verificable por tercero.
