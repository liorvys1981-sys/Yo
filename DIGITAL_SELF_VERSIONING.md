# DIGITAL SELF — VERSIONADO

## Modelo

- `set()` crea versión N+1; la versión anterior **se preserva intacta** (nunca se edita).
- `active_version` apunta a la última; `version(n)` accede a cualquiera.
- `EntityVersion.content_hash`: sello SHA-256 del contenido canónico en el momento del commit.
- `verify_integrity()`: recalcula y lanza `VersionIntegrityError` si el contenido fue mutado tras el sellado (dicts anidados de Python no son congelables: integridad por **detección**, no prevención — decisión documentada, coherente con la filosofía evidence del ecosistema).

## Reconstrucción

- `entity.as_of(ts)` → última versión vigente en ts (None si anterior a la primera).
- `DigitalSelf.reconstruct(ts)` → snapshot de las 7 entidades como estaban en ts.
- Revert = crear una versión nueva que restaure contenido anterior (nunca editar el historial).

## Reglas fundamentales

Identity y Values: toda transición en `evolution` con `approved_by != "humano"` es rechazada por el validador (genome.py comparte esta regla).
