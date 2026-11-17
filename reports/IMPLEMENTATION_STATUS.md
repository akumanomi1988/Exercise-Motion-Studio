# Estado de implementación

Actualizado: 2026-11-17 — HEAD del bootstrap: `a7c96a2519b4f1711f8a25fbbf20167549a1cf28`.

**Resultado global: IN_PROGRESS — MoCap NO IMPLEMENTADO.**

| Gate | Estado | Evidencia / Pendientes |
|---|---|---|
| G0: entorno limpio Windows, CLI, tests, auditoría | IN_PROGRESS | Bootstrap Python PASS 9/9 en Linux CI; falta instalación real Windows/Blender/FFmpeg/.NET, locks y auditoría |
| G1: movimiento, dos avatares, T01–T03 | NOT_STARTED | No existe captura/retarget/render real |
| G2: equipamiento libre T04–T08 | NOT_STARTED | No existen modelos/contactos |
| G3: máquinas T09–T10 | NOT_STARTED | Faltan plantillas y licencias |
| G4: piloto 10/10 | NOT_STARTED | Faltan diez vídeos autorizados y aprobación |
| G5: importación snapshot Kinetic | NOT_STARTED | No se ha ejecutado inventario |
| G6: 100 % catálogo Kinetic | NOT_STARTED | Sin medios finales |
| G7: integración Anvil/Supabase | BLOCKED | Requiere autorización separada |

**CI verificada:** [Bootstrap Python checks](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44094428263) — SUCCESS sobre commit `a7c96a2`; 9 tests unitarios en 0,015 s (Python 3.11, ubuntu-latest), compileall y doctor sin fallos.

**Qué prueban esos tests:** registro de vídeo local, declaración de derechos, no aprobación comercial, hash/idempotencia, extensiones, ID y diagnósticos. **No prueban:** vídeo decodificable, pose, 3D, Blender, WebP, hardware Windows ni viabilidad comercial de assets.

Hitos y trabajo futuro: [Issues del repositorio](https://github.com/akumanomi1988/Exercise-Motion-Studio/issues).