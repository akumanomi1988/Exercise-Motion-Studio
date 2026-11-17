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
