# Estado de implementación

Actualizado: 2026-11-17 — I0.1 integrado en main `423262c`; AG0 inicial en PR #10 (`1078584` CI verificada).

**Resultado global: IN_PROGRESS — MoCap NO IMPLEMENTADO.**

| Gate | Estado | Evidencia / Pendientes |
|---|---|---|
| G0: entorno limpio Windows, CLI, tests, auditoría | IN_PROGRESS | Registro + decodificación completa de vídeos mediante FFmpeg; Linux CI PASS 15/15 (run 44103138578). Falta Windows real/Blender/.NET, locks y auditoría de distribución |
| G1: movimiento, dos avatares, T01–T03 | NOT_STARTED | No existe captura/retarget/render real |
| G2: equipamiento libre T04–T08 | NOT_STARTED | No existen modelos/contactos |
| G3: máquinas T09–T10 | NOT_STARTED | Faltan plantillas y licencias |
| G4: piloto 10/10 | NOT_STARTED | Faltan diez vídeos autorizados y aprobación |
| G5: importación snapshot Kinetic | NOT_STARTED | No se ha ejecutado inventario |
| G6: 100 % catálogo Kinetic | NOT_STARTED | Sin medios finales |
| G7: integración Anvil/Supabase | BLOCKED | Requiere autorización separada |

**CI verificada:** [Python and media ingestion checks](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44103138578) — SUCCESS sobre `99381f4`; 15 tests (Python 3.11, Ubuntu 26.04, FFmpeg 8.0.1), compileall y doctor. La primera CI en PR #9 falló por FFmpeg ausente en el runner y se reparó instalándolo explícitamente.

**Qué prueban esos tests:** registro, derechos atestiguados pero no aprobados, hash/idempotencia, extensiones, ID, diagnósticos, metadatos ffprobe, decodificación FFmpeg de un patrón de vídeo codificado, rechazo de MP4 falsos y detección de cambios de fuente. **No prueban:** vídeo real de ejercicio, landmarks, pose, 3D, Blender, WebP, hardware Windows ni viabilidad comercial de assets. El fixture codec generado NO satisface T01–T10.

Hitos y trabajo futuro: [Issues del repositorio](https://github.com/akumanomi1988/Exercise-Motion-Studio/issues).
## AG0 / asset inicial — parcial, NO gate aprobado
- Generador procedural original de mancuerna hexagonal 10 kg parametrizable (`src/blender/generate_hex_dumbbell.py`), sin dependencias de modelos de terceros.
- [Blender 5.0.1 headless CI PASS](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44105697508): creado `asset.blend`, `asset.glb`, `preview.png`, `asset.json`, `qa_report.json`; cinco mallas, cinco mallas reimportadas, materiales presentes y preview no uniforme.
- [Python CI PASS 23/23](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44105697672): controles de manifiesto, derechos, integridad de hashes y acceso seguro. Artefactos de prueba de manifiesto NO representan activos reales.
- Revisión visual humana, uso con avatares y aprobación comercial: PENDING. No se ha integrado ningún modelo en una rutina.
- **AG0 = IN_PROGRESS; AG1–AG5 = NOT_STARTED; G0 = IN_PROGRESS; G1–G6 = NOT_STARTED.**
