# Resultados de pruebas — evidencias

## 2026-11-17 — CI bootstrap

- **Commit probado:** `a7c96a2519b4f1711f8a25fbbf20167549a1cf28`.
- **Run:** [Bootstrap Python checks — SUCCESS](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44094428263).
- **Entorno:** GitHub Actions `ubuntu-latest`; Python 3.11.
- **Comandos:** `python -m compileall -q src/motion_pipeline/ems`; `PYTHONPATH=src/motion_pipeline python -m unittest discover -s tests/unit -v`; `python -m ems doctor`.
- **Resultado:** 9 pruebas ejecutadas; 9 PASS, 0 FAIL, 0 ERROR. Salida unittest `Ran 9 tests in 0.015s / OK`.
- **Cobertura:** sólo registro, validación inicial, hash, manifest, idempotencia y doctor.
- **No verificado:** Windows local, ffmpeg/blender reales, licencia de pesos de IA, decodificación, MoCap, QA biomecánico, exportación, GLB, WebP, PNG o YouTube.

**Decisión:** bootstrap CI PASS. **Gate G0 permanece IN_PROGRESS.** Ningún G1–G7 ha pasado.

## Próximos resultados exigidos

Registrar comandos y versiones para Windows 10/11, vídeos reales autorizados, rig y assets propios/verificados, hash de exportaciones, screenshots y revisión visual, junto con los flags PASS/FAIL/BLOCKED.
## 2026-11-17 — I0.1: FFprobe + decodificación completa de vídeo

- **Commit CI:** `99381f4775876078107f5f4c648924d57b6a4817`.
- **Primera ejecución fallida:** [44102986758](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44102986758): `command -v ffmpeg` exit 1 en runner ubuntu-26.04; tests de esa ejecución no llegaron a ejecutarse.
- **Segunda ejecución satisfactoria:** [44103138578](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44103138578): 15 pruebas, 0 fallos, 0 errores, 0 omitidas observadas en log; `Ran 15 tests in 0.564s / OK`.
- **Entorno:** GitHub Actions Ubuntu 26.04 LTS, CPython 3.11.18, FFmpeg/FFprobe 8.0.1-3ubuntu2.
- **Comandos ejecutados:** `python -m compileall -q src/motion_pipeline/ems`, `python -m unittest discover -s tests/unit -v`, `python -m ems doctor`. Se comprobaron binarios ffmpeg/ffprobe.
- **Verificaciones nuevas:** clip de codec 64x48, MPEG4, 12 FPS, decodificación `decoded_frames > 0` y `FULL_STREAM_DECODED`; SHA registrado consistente, error al manipular archivo, error con falso MP4, ID inseguro y timeout inválido rechazados.
- **Decisión:** prueba de integración de códec/media = PASS en Linux. **G0 sigue IN_PROGRESS. G1 no probado.** Clip sintético de CI NO reemplaza vídeo humano autorizado, render 3D ni inspección visual.

## 2026-11-17 — AG0.1: generación 3D real y validación de integridad

- **Commit evaluado:** `1078584b671b3887250265f00993555a3fe33bb7` (PR #10).
- **Primera ejecución Blender:** [44104444811](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44104444811) FAIL: `ModuleNotFoundError: No module named 'numpy'` al exportar GLB; instalado `python3-numpy` explícitamente.
- **Ejecución final Blender:** [44105697508](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44105697508) PASS en Blender 5.0.1, NumPy 2.3.5, Ubuntu 26.04. Comandos: `blender -b --factory-startup --python-exit-code 10 --python src/blender/generate_hex_dumbbell.py -- --output-dir data/generated_assets/hex-10kg --mass-kg 10` y `blender -b --factory-startup --python-exit-code 10 --python tests/asset/qa_hex_dumbbell.py -- --asset-dir data/generated_assets/hex-10kg`.
- **Métricas:** 5 mallas originales y 5 importadas desde GLB, 512×512 PNG con contenido no uniforme, dimensiones renderizadas X/Y/Z `[0.47, 0.167689, 0.147224]` metros. Archivo Blender y GLB abiertos headless; hashes persistidos en asset.json.
- **Artefacto técnico disponible 7 días:** [original-hex-dumbbell-10kg-technical-unreviewed](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44105697508/artifacts/14338461498). El archivo generado NO queda publicado como asset comercial permanente.
- **Validación independiente del artefacto descargado:** trimesh encontró cinco geometrías, con bounding box compatible; tras unificar vértices divididos por normales/UV, las cinco mallas son watertight. Preview PNG abierto e inspeccionado; reconocimiento de mancuerna confirmado; calidad comercial NO aprobada.
- **Suite Python:** [44105697672](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44105697672) PASS, `Ran 23 tests in 0.622s / OK`.
- **Decisión:** generación de UN equipo de peso libre y QA técnico = PASS. **AG0/G2 NO están aprobados**: sin avatares, grip animado, revisión humana de calidad/licencias, ejecución Windows ni piloto real.
