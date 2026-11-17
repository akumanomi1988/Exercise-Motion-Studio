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