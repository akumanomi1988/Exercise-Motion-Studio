# Registro de iteraciones

## I0 — 2026-11-17 — inicialización y bootstrap

- Repo vacío inicializado con README, especificación íntegra y AGENTS.md.
- Publicados arquitectura, política comercial, QA biomecánico y plan Kinetic.
- Añadido CLI Python 0.1.0: doctor y registro local de fuentes con SHA-256 e idempotencia.
- Derechos registrados exclusivamente como USER_ATTESTED; nunca se interpreta como aprobación comercial.
- Datos privados excluidos de Git; sin código de descarga YouTube.
- Añadidos scripts PowerShell, tests stdlib y GitHub Actions ligero.
- CI SUCCESS [run 44094428263](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44094428263) con nueve tests unitarios.
- Creados issues #1–#7 para los gates y dependencias.
- No hay todavía captura, retargeting, animación ni render real. G0 sigue IN_PROGRESS.

Próxima ejecución: verificación Windows, revisión de licencias/pesos, contratos de movimiento y primer vídeo autorizado.
## I0.1 — 2026-11-17 — comprobación real de contenedores y códecs

- Inicio: `register` permitía un MP4 no decodificable, por diseño del bootstrap. Captura G1 no podía confiar en los inputs.
- Implementado `ems probe --job-id` en `src/motion_pipeline/ems/media.py`: SHA de entrada, FFprobe (códec, FPS, dimensiones, duración), decodificación de todos los fotogramas con FFmpeg, escritura atómica de `media_probe`; no eleva derechos o G1.
- Añadidos seis tests de integración con clip de patrón producido por FFmpeg durante CI; este clip NO es ejercicio humano y no computa para G1.
- Intento 1: [run 44102986758](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44102986758) FAIL, runner ubuntu-26.04 no tenía FFmpeg.
- Corrección: instalar FFmpeg con apt en el workflow. Intento 2: [run 44103138578](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44103138578) SUCCESS, 15/15.
- Licencias: registrados FFmpeg y FFprobe como dependencias externas PENDING, sin atribuirles aprobación comercial para su redistribución.
- Limitaciones: sin validación Windows ni vídeos de ejercicio autorizado. Siguiente requisito: modelo de pose licenciado y reconstrucción de landmarks sobre un vídeo T01 autorizado.

## AG0.1 — 2026-11-17 — primer activo 3D original verificable

- Implementado generador Blender de una mancuerna hexagonal con parámetros, cinco piezas diferenciadas, grip center, tres colisionadores cilíndricos y dos contactos exteriores.
- Salida reproducible por comando: `.blend` editable, `.glb` de distribución técnica, render PNG y `asset.json` con hashes SHA-256 y derechos PENDING.
- Intento inicial: [run 44104444811](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44104444811) FAIL, Blender 5.0.1 instalado sin NumPy; falla el exportador glTF. Se corrigió instalando `python3-numpy` y `python3-pil`.
- Iteración: se añadió QA headless de importación GLB, reapertura del .blend, mallas finitas, materiales y PNG no uniforme; se añadieron superficies de contacto y colisionadores físicos.
- Contrato AG0: `src/motion_pipeline/ems/catalog.py`, CLI `asset-check` y 8 tests unitarios contra falsificación de hashes, duplicados, manipulación de rutas y derechos pendientes.
- CI final: [Blender PASS](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44105697508), [Python 23/23 PASS](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44105697672), commit `1078584`.
- GLB descargado y verificado externamente con trimesh: cinco geometrías, cuerpos cerrados tras soldar vértices de seams normales/UV; PNG inspeccionado manualmente en revisión técnica asistida. **No cuenta como aprobación visual humana comercial.**
- Restan rig/animación, maquinaria, más activos, compatibilidad con ambos avatares, licencias definitivas y revisión de calidad comercial. AG0 sigue IN_PROGRESS.
