# YO CLONE — REPOSITORY AUDIT

Fecha: 2026-10-09T17:35:39.325772+00:00Z · Método: git clone --depth 1 real de los 3 repos + inspección de archivos + API GitHub (rate limit 60/60 alcanzado parcialmente). Ningún modelo ejecutado (sin GPU/weights en sandbox).

## Resumen por repo
| Repo | Existe | Licencia | Actividad | Naturaleza |
|---|---|---|---|---|
| PunithVT/ai-avatar-system | VERIFICADO (clone OK) | MIT (VERIFICADO) | 2026-09-18 (activo) | Plataforma full-stack avatar en tiempo real (FastAPI + React + musetalk + TTS + docker) |
| ChenleWang123/LiveTalking | VERIFICADO (clone OK) | Apache-2.0 (VERIFICADO) | 2026-09-10 (activo; fork de lipku/LiveTalking) | Motor de talking-face real-time (Flask + aiortc WebRTC + edge_tts) |
| JabranMustafa/twin-mind-mirror | VERIFICADO (clone OK) | **SIN LICENCIA** | 2026-03-09 (ESTANCADO) | Webapp chatbot "personalidad digital" (React+Supabase); **sin capacidad visual** |

## Hallazgos clave (verificados por inspección de archivos reales)
1. **ai-avatar-system**: backend Python con `musetalk_worker.py`, workers TTS, `pytest.ini`, frontend TSX, docker-compose + nginx + infra. MIT limpio (sin .env commiteado).
2. **LiveTalking**: 156 archivos .py, `app.py` con aiortc (WebRTC real-time), `edge_tts` (TTS por servicio externo — no soberano), `benchmark_asr.py`. Pesos de modelos NO incluidos (descarga externa).
3. **twin-mind-mirror**: **`.env` commiteado** con claves Supabase (publishable key — riesgo de abuso, mala práctica grave). **Sin LICENSE** → no usable legalmente. No genera réplica visual alguna.

## Fuentes y versiones
- Commits examinados: ai-avatar-system `0dee976c229b` · LiveTalking `ec2e425132c` · twin-mind-mirror `4c588caad2` (todos HEAD al 2026-10-09).
- Clones locales (aislados): /tmp/repo_audit/<repo> (efímeros; hashes de referencia en MATRIX).

## Pruebas ejecutadas
Inspección estática real (archivos, licencias, deps, estructura). Ningún test del repo ejecutado (deps pesadas sin GPU). Ningún modelo corrido.

## Riesgos
- Pesos de musetalk/wav2lip: licencias propias NO VERIFICADAS (BLOQUEADO).
- LiveTalking depende de `edge_tts` (servicio externo Microsoft) → conflicto con soberanía si se usa por defecto.
- ai-avatar-system: superficie amplia (OTel, infra, nginx) → auditoría de seguridad pendiente antes de cualquier integración.
