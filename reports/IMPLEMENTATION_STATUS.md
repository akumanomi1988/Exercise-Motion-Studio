# Estado de implementación

Actualizado: 2026-11-17 — main validado `ef1b1d0`; nueva I1.1 en PR #11, validación CI `f64a61f`.

**Resultado global: IN_PROGRESS — captura de pose 3D REAL implementada y probada; retargeting humanoide y catálogo NO completados.**

| Gate | Estado | Evidencia / Pendientes |
|---|---|---|
| G0: entorno limpio Windows, CLI, tests, auditoría | IN_PROGRESS | Registro + decodificación completa de vídeos mediante FFmpeg; Linux CI PASS 15/15 (run 44103138578). Falta Windows real/Blender/.NET, locks y auditoría de distribución |
| G1: movimiento, dos avatares, T01–T03 | IN_PROGRESS | Captura real 46/47 fotogramas, 33 landmarks 3D relativos y GLB diagnóstico animado. Faltan skeleton canónico, retarget a dos rigs reales, contactos y T01–T03 con QA humano |
| G2: equipamiento libre T04–T08 | NOT_STARTED | Una mancuerna 3D procedural técnicamente validada, sin contacto animado ni licencia/aprobación comercial firmada |
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

## I1.1 — primera captura humana real y cadena visual técnica

- **[Real-video Pose + Blender CI SUCCESS](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44109871802)** (commit `f64a61f`): clip humano independiente CC BY-SA; 47 fotogramas, 46 detecciones (97,8723 %), 33 landmarks por pose, media visibilidad core 0,899091. Trayectoria vertical de tobillo relativa 0,356798 m.
- **Salida** `pose_raw.json` con origen, modelo/hash, tiempos, visibility/presence y landmarks hip-relative. No contiene rotaciones de rig normalizado ni root motion absoluto.
- **GLB diagnóstico no comercial**: 51 objetos / 51 acciones reales, reimport Blender PASS con transformación no estática (desplazamiento cuadrático 0,1680697); PNG 512x512 y WebP animado de 8 frames. [Artifact 14341415126](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44109871802/artifacts/14341415126), solo 7 días.
- **[Python CI PASS 32/32](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44109871808)**. Estos tests de contratos NO sustituyen el E2E real.
- **Inspección de preview:** el sujeto presenta flexión/extensión, pero hay inestabilidad de segmentos y longitud visual. Biomecánica, articulaciones, escala y sincronización aún NO aprobadas.
- **G0 IN_PROGRESS, G1 IN_PROGRESS. AG0 IN_PROGRESS. G2–G6 NOT_STARTED. G7 BLOCKED.** Ningún avatar hombre/mujer comercial apto incluido; la visualización de landmarks NO es un avatar.
