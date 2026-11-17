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

## 2026-11-17 — I1.1: primer E2E real human-inference y export GLB diagnóstico

- **Python checks:** [run 44109871808](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44109871808) SUCCESS; `Ran 32 tests in 0.637s / OK`. Son validaciones del contrato, no scoring biomecánico.
- **Comando smoke:** `PYTHONPATH=src/motion_pipeline python tests/integration/smoke_real_pose.py --video data/qa-inference/real_single_leg_squat.webm --model data/qa-inference/models/pose_landmarker_full.task --model-sha256 5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1 --qa-output data/qa-inference`.
- **Fuente humano real:** Wikimedia Commons `Basic single leg squat.webm`, autor RickyBennison, CC BY-SA 4.0, SHA-256 `ab4602823ad00de3409eb50d2c65c6b1ce5566c5dca6753555ff2b19107db88e`. Obtenido legalmente desde Commons para ensayo (no YouTube). T01–T10 **NO** declarados aprobados.
- **Modelo real:** MediaPipe 0.10.35 CPU, bundle Full float16/v1 y SHA `5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1`.
- **[Run 44109871802](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44109871802) — SUCCESS:** `REAL_VIDEO_POSE_SMOKE_PASS` con 47 frames, 46 poses detectadas, cobertura `0.978723`, visibilidad media core `0.899091`, span vertical tobillo relativo `0.356798m`, hash pose `ce84580adce891401f49647bc412256b48f797531e2824b49584c44f8bbb2c20`.
- **Blender diagnóstico:** `blender -b --factory-startup --python-exit-code 10 --python src/blender/visualize_raw_pose.py -- --pose-raw data/qa-inference/pose_raw.json --output-dir data/qa-inference/diagnostic`; 51 mallas/51 acciones animadas en GLB, intervalo de 47 frames, 8 renders de 512x512.
- **Re-import y QA:** `blender -b --factory-startup --python-exit-code 10 --python tests/asset/qa_pose_debug.py -- --asset-dir data/qa-inference/diagnostic` => `TECHNICAL_PREVIEW_PASS`, 51 mallas y acciones, cambio de traslaciones al reproducir (`world_translation_displacement_sq = 0.1680697`). `python scripts/encode-pose-preview.py --asset-dir data/qa-inference/diagnostic` => WebP con 8 frames, 31.708 bytes.
- **Artefactos temporales (7 días):** [GitHub artifact 14341415126](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44109871802/artifacts/14341415126): `pose_debug.glb` (335.992 bytes), `pose_debug.png` (145.031 bytes), `pose_debug.webp` (31.708 bytes), `debug_manifest.json`, `SOURCE_ATTRIBUTION.txt`. Ningún vídeo de tercero ni pesos de IA publicado.
- **Inspección visual técnica:** la captura 3D muestra flexión/extensión; se observan links no biomecánicos, segmentos de longitud inconsistente y ausencia de rig/IK. NO cumple los criterios VAL-03/05/06/11/12 ni prueba de avatars hombre/mujer.
- **Fallo diagnosticado y corregido:** `ffprobe` ausente → instalar FFmpeg; `libGLESv2.so.2` ausente → instalar runtime EGL/GLES; OpenImageDenoiser ausente → deshabilitar denoising en render técnico. No se relajaron los umbrales del smoke.
- **Resultado:** captura de vídeo real, GLB diagnóstico reimportable y WebP animado = PASS técnico. **Gate G1 = IN_PROGRESS, no aprobado. Sin motion.json final, rigs, contacto ni compatibilidad de visor React/Three.js.**

## 2026-11-17 — I1.2: esqueleto intermedio y visualización original/normalizada

- **CI unit tests final:** [44113258264](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44113258264), `Ran 41 tests in 0.599s / OK` en Python 3.11 Linux. Incluyen tests de geometría, contratos, derechos y auditoría temporal; NO sustituyen prueba real.
- **CI real final:** [44113258239](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44113258239) SUCCESS en todo el pipeline: FFmpeg → MediaPipe 0.10.35 CPU con vídeo humano Commons CC BY-SA → raw pose → solver → Blender raw/solved GLB → reimport → PNG y WebP.
- **Observaciones:** 47 frames/46 detectados; cobertura 0,978723; variación máxima segmental original 0,441919; variación máxima resuelta 0,0 (reproyección exacta, NO precisión fisiológica). Máxima velocidad angular medida 504,907872 grados/s; cinco eventos sobre umbral de cribado 450 grados/s; 86 muestras segmentales de baja visibilidad.
- **GLB original:** 51 mallas/51 acciones, 8 PNG muestreados, WebP ocho frames y 31.708 bytes. **GLB resuelto:** 33 mallas/33 acciones reimportadas con cambios de traslación; 8 renders, WebP ocho frames y 24.280 bytes. Ambos diagnósticos sin avatar humano, sin revisión biomecánica ni licencias comerciales aprobadas.
- **Artifact original y resuelto:** [14340628838](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44113258239/artifacts/14340628838) (retención 7 días). Incluye `solved_skeleton.json` y `SOURCE_ATTRIBUTION.txt`, además de dos GLB y previews; no incluye vídeo original ni pesos descargados.
- **Seguridad:** `solved_skeleton.json` se genera sólo sobre captura real coincidente con hash de job y fuente; `review.status = REVIEW_REQUIRED`. T01 bilateral/T02/T03 y dos avatares **no se han ejecutado**; G1 NO aprobado.

## 2026-11-17 — AG1.1: dos humanos CC0 riggeados (PR #13)
- [CI SUCCESS 44117210502](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44117210502), Blender 5.0.1, MPFB pinned `9de0707fdc88438d7c53a1a2ac7937d9221e2431`.
- Comandos reales en `.github/workflows/avatar-ci.yml`: Blender headless `build_mpfb_avatars.py --variant male|female`, seguido de `qa_mpfb_avatar.py` por variante y `qa_dual_avatar.py`.
- Output masculino: 19.158 vértices originales, 53 bones, 3.088.392 bytes GLB, deformación máxima experimental al rotar hueso `head` de 0,222905 m. Femenino: 19.158, 53 bones, GLB 3.088.796 bytes, 0,257208 m. 53 nombres de hueso compartidos, distintas geometrías.
- Evidencia temporal [artifact 14344455745](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44117210502/artifacts/14344455745); `human_visual_review=PENDING`, `pose_retarget=NOT_TESTED`, `commercial_approval=false`. AG1 IN_PROGRESS.

## 2026-11-17 — AG2.1: barra olímpica, loaded/unloaded (PR #14)
- [CI SUCCESS 44117688418](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44117688418): Blender ejecutó `generate_olympic_barbell.py` con `--plate-mass-kg 20 --plates-per-side 0` y `1`, y `qa_olympic_barbell.py` sobre ambos `.blend`/`.glb` y PNG.
- Output real: 20 kg, 7 mallas, envelope `[2.2, 0.078, 0.078]` m; 60 kg, 9 mallas, envelope `[2.2, 0.45, 0.45]` m, orificio anular de discos CHECKED. Imágenes 960x480 con píxeles no uniformes. CI de `ems asset-check --require-commercial` rechaza las dos variantes PENDING correctamente.
- [Artefacto CI 14343532475](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44117688418/artifacts/14343532475) con GLB, fuentes .blend, previews y QA. `dual_avatar_grips=NOT_TESTED`, sin contacto real ni revisión humana. AG2 IN_PROGRESS, no aprobado.

## 2026-11-17 — G1.2 real human-to-skin retarget (experimental PR #16)
- CI 44120835127 **SUCCESS técnica**: 47 frames del vídeo legítimo de sentadilla a una pierna (46 detectados), 16 huesos mapeados, dos avatares de 53 huesos, GLB de 3.145.240 / 3.145.864 bytes, 8 frames PNG y WebP animado por avatar, archivo .blend editable y manifest con SHA/licencia CC BY-SA 4.0. QA importada calculó desplazamientos de malla animada de 1,147209 m y 1,052190 m, refutando un GLB estático.
- Artefacto CI 14345087065 revisado visualmente con previsualizaciones PNG/WebP reales: **FAIL** por colisiones, torsiones y estiramientos no anatómicos. NUNCA convertir este PASS técnico en PASS biomecánico o comercial.
- CI 44121806410 **SUCCESS técnica** tras calibración relativa y hold de segmentos ocultos. Artefacto 14346355960 revisado visualmente: **FAIL**; mejora de ciertos ejes, pero persiste severa deformación de cadera/piernas. Datos de calidad entran en cola de revisión, no en distribución.
- Ensayos en curso: comparar geometría del bind-rest de GLB importado con pose de referencia animada. Resultado pendiente. G1 **NOT_APPROVED**, integración Kinetic NO INICIADA para estos recursos.

## 2026-11-17 — AVATAR BIND-REST CIERRE TÉCNICO + RETARGET VISUAL FAIL
- PR #18, CI SUCCESS 44124085638. Unweighted skinned MPFB real original en `.blend` frente a GLB reimportado: 13380 vértices de malla original evaluada, 14765 en GLB tras splitting. Distancia geometría evaluada P95 0,0000005 m, P99 y máxima 0,0000007 m, ambos. Rig 53 huesos, test de deformación real PASS, GLB male 949312 bytes, female 948912 bytes. Test de regresión permanente en `tests/asset/qa_mpfb_bind_rest_fidelity.py`.
- PR #16, CI SUCCESS 44124440610 y artifact 14346548007: 47 fotogramas de persona real, 46 detectados, 16 bones animados sobre los avatares saneados, GLB/PNG/WebP producidos y reimportados. QA automatizada de malla en movimiento PASS.
- **Revisión humana de 8 vistas animadas: FAIL** por torsión excesiva y posturas inverosímiles en partes del ciclo. La exactitud de fuente y bind-rest no garantiza retarget de calidad. Se requieren controles de pose-neutral, límites articulares, confianza de segmentos, estabilidad temporal y contacto. NO SUBIR A BIBLIOTECA KINETIC.
