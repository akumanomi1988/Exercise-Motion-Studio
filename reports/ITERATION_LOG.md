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

## I1.1 — 2026-11-17 — captura real y primer diagnóstico GLB desde un humano

- Fuente real: `Basic single leg squat.webm` de RickyBennison (obra propia Wikimedia Commons, CC BY-SA 4.0). Sólo como test, no se distribuye original ni se presenta como vídeo propio. SHA-256 `ab4602823ad00de3409eb50d2c65c6b1ce5566c5dca6753555ff2b19107db88e`.
- Modelo: Google MediaPipe Pose Landmarker Full float16/v1, `mediapipe==0.10.35`, SHA-256 `5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1`. Google confirma Apache 2.0 del modelo en https://github.com/google-ai-edge/mediapipe/issues/6306. Se descarga con hash fijo al ejecutar instalación opcional; no se incluye en Git.
- Implementado `ems capture`: exige manifest de fuente y FFmpeg probe completo, comprueba hash vídeo/modelo; inferencia VIDEO CPU sobre frames RGB CFR; 33 landmarks 2D y 3D hip-relative en `pose_raw.json` con confianza por punto y segmento. Sujetos múltiples → `AMBIGUOUS`, no selección arbitraria. Mantiene `USER_ATTESTED` y `REVIEW_REQUIRED`.
- Intento A [run 44108470794](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44108470794) FAIL: ffprobe ausente en runner; reparado instalando FFmpeg explícitamente.
- Intento B [run 44109069768](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44109069768) FAIL: librería nativa MediaPipe requiere `libGLESv2.so.2`; reparado instalando libgles2/libegl1/libgl1.
- Intento C [run 44109485096](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44109485096): PASÓ inferencia real de 46/47 fotogramas; después falló el render Blender por OpenImageDenoiser no presente. Solución: deshabilitar denoising exclusivamente en el visualizador de diagnóstico.
- Intento D [run 44109871802](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44109871802) SUCCESS completo: MediaPipe real → pose_raw → Blender GLB 51 objetos animados → Blender GLB round-trip → PNG y WebP 8 frames. Artifacts https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44109871802/artifacts/14341415126
- Se inspeccionaron PNG y contacto visual de 8 frames. Movimiento detectado y alternancia de flexión/extensión, pero links cruzados, geometría no anatómica y ausencia de estabilización/calibración. Este GLB **es un diagnóstico de landmarks, no un avatar**, ni una prueba G1 PASS.
- El CI Python [run 44109871808](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44109871808) ejecutó 32 tests, todos PASS. El ensayo con vídeo real es independiente de tests unitarios con fixtures.
- Próximo requisito G1: resolver esqueleto local normalizado e IK con duraciones/huesos consistentes y dos avatares riggeados comercialmente autorizados. Distinguir artefactos de diagnóstico de exportaciones aprobadas.

## I1.2 — 2026-11-17 — solver sobre captura humana real

- Se implementó `ems solve` y `src/motion_pipeline/ems/solver.py`: extrae el esqueleto intermedio de 17 anclajes/16 segmentos de `pose_raw.json` real, con longitudes medianas de frames visibles; mantiene fotogramas `MISSING` sin inventar medidas, marca baja visibilidad y no atribuye root motion absoluto ni twist anatómico.
- Se añadieron ocho pruebas algebraicas, una prueba específica de screening temporal y ejecución E2E tras captura MediaPipe sobre vídeo real. Primer resultado [run 44112181374](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44112181374): PASS con 40/40 tests Python [run 44112181863](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44112181863).
- Se extendió QA con estadísticas por segmento y velocidad angular en grados/s; el cambio de estructura en `prior_dirs` provocó fallos reproducidos en seis tests; se corrigió el acceso a (dirección, timestamp) en commit `45e2967`, sin reducir umbrales.
- Se creó `src/blender/visualize_solved_skeleton.py` para exportar el esqueleto de segmentos fijados como GLB animado diagnóstico y renderizar ocho frames. El test ya existente de importación GLB corrió también contra esta escena y verificó movimiento real.
- Resultados finales [Python 44113258264](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44113258264) PASS 41/41; [vídeo humano + Blender 44113258239](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44113258239) SUCCESS todos los pasos. Diferencia original 44,1919 % de longitud en el peor segmento, corregida geométricamente a 0 %; 86 muestras de baja visibilidad y cinco eventos angular alta >450 grados/s. **Requiere revisión, no biomecánica PASS**.
- Se explicitó CC BY-SA 4.0 de todos los derivados de la grabación Commons en `SOURCE_ATTRIBUTION.txt`. Ninguna fuente original subida a Git. Siguiente: retarget a avatares con skinning comercialmente aptos, IK y QA de contacto.

## AG1.1 — 2026-11-17 — generación de dos avatares realmente riggeados
- PR #13: https://github.com/akumanomi1988/Exercise-Motion-Studio/pull/13 — merge main `3ba87c7`.
- Falla inicial CI 44115908738: MPFB instalado como add-on clásico cuando exige extension `bl_ext.user_default.mpfb`. Segunda falla CI 44116459968: `--factory-startup` vaciaba las preferencias de extensión. Se instaló y habilitó la extensión correctamente y se ejecutó Blender sin esa opción durante build.
- CI final 44117210502 SUCCESS: humanos masculino y femenino, GameEngine rig compartido de 53 huesos, 19.158 vértices skinned y deformación real al rotar hueso en asset reimportado. Ambos casos técnicamente probados.
- Bloqueos persistentes: retarget desde vídeo, IK, QA biomecánica, revisión de apariencia y derechos de distribución final. Ningún cambio en Anvil/Supabase. AG1 NO aprobado.

## AG2.1 — 2026-11-17 — primera barra olímpica original, 2 variantes
- Nuevo `src/blender/generate_olympic_barbell.py` en PR #14, parametrizado por masa nominal de disco (5/10/15/20/25) y número de discos por lado (0..4). Anillos procedurales con huecos pasantes reales en lugar de cilindros macizos intersectando la barra.
- Cada variante exporta `asset.blend`, `asset.glb`, `preview.png` y `asset.json` con hashes, dos agarres a ±0,42 m, colisionadores y procedencia.
- Corrección previa a CI: ajustar ancho/alto de envelope de la barra sin discos a la geometría real del collar (0,078 m), no al diámetro del disco de la configuración seleccionada.
- CI final 44117688418 SUCCESS: builds 20/60 kg, round-trip GLB, topología de discos, material, dimensiones y píxeles de render. Prueba comercial fail-closed confirma ausencia de aprobación.
- No hay animación ni grip constraint probado; no declarar AG2/G2 PASS. El material es original procedural, sin recursos 3D de terceros.

## AG1.2/G1.2 — 2026-11-17 — evaluación real y fallo visual documentado
1. PR #15 integró el mapeo correcto de género tras detectar inversión en MPFB `macro.json` que QA estructural no había detectado. CI 44118646868 PASS.
2. PR #16 implementó un retarget experimental con 16 huesos sobre dos GLB MakeHuman skinned reales, usando `solved_skeleton.json` del vídeo CC BY-SA real de Wikimedia (46/47 observaciones), y verificación de movimiento de malla al reimportar.
3. CI 44120835127 SUCCESS en pruebas técnicas; cifras de desviación máxima de vértices importados 1,147209 m (male) y 1,052190 m (female). El examen visual de los PNG/WebP reales encontró cuerpos deformados, piernas incongruentes y penetraciones severas. **Visual FAIL**.
4. Ajuste experimental de swings relativos a un frame de referencia, omisiones de segmentos de baja confianza y límites de velocidad angular. CI 44121806410 SUCCESS técnico, pero inspección visual externa del artifact 14346355960 sigue mostrando graves deformaciones. **Visual FAIL**.
5. Nueva prueba en progreso distingue render de bind-rest del GLB importado de la malla retargeteada en pose neutral. Foco: skinning/inverse bind y transformaciones jerárquicas; no dar por completado G1 sin corregir artefactos visuales.
6. No se ha publicado ningún recurso retargeteado comercialmente ni se han modificado Anvil Fitness/Supabase.

## AG1.3 — 2026-11-17 — corrección causal del GLB, verificación y nuevo bloqueo
- Aislamiento diferencial de artefactos: el .blend MakeHuman mostraba miembros normales, el GLB importado contenía geometría helper de falda/cabello no visible en source render. El test anterior de skin validaba huesos y pesos, pero no comparaba superficie en bind-rest.
- PR #18: `export_apply=True` al glTF export aplica Mask y elimina helpers preservando Armature. GLB male 949312 bytes, female 948912 bytes; 53 huesos, skin deformación real, CI 44124085638 PASS. Comparador de superficies (KDTree) fuente 13380 vértices evaluados / GLB 14765 con material splits: p95=0,0000005 m, p99=0,0000007 m, máximo=0,0000007 m ambos avatares.
- PR #16 retarget rerun 44124440610 SUCCESS técnica con GLB saneados. Artefacto 14346548007 inspeccionado con 8 imágenes por avatar: desaparece geometría de falda, PERO movimientos de hombros, tronco, cadera y piernas en ciertos fotogramas siguen biomecánicamente incorrectos. No fusionar PR #16 hasta solucionar referencia-neutral/rotation-swing y oclusión. Ni G1 ni comercial aprobados.

## G1.4 — 2026-11-18 — raíz vertical del avatar y test GLB de contacto parcial

1. Se comprobó `main=81c1e3b5`, informes, política de licencias, PR #16 e historial de CI. Últimos renders de retarget permanecían rechazados visualmente.
2. En PR #16 se añadió raíz Z desde el dedo del pie visible más bajo, con retención explícita ante oclusión (`a94452bc`); no infiere root absoluto ni bloquea pies en el plano horizontal.
3. Se añadió QA estricta tras **reimportar** GLB: error máximo de altura del apoyo <=0,03 m en todas las observaciones válidas, además de procedencia y derechos bloqueantes (`c7325aa3`).
4. [CI 44253025285](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44253025285) FAIL antes de exportación por cuaterniones equivalentes 0°/360° interpretados como torsión; otra corrección de la rama `49720b40` lo solventó sin desactivar la comprobación.
5. [CI 44253263080](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44253263080) SUCCESS técnico, 2 avatares/GLB/WebP, pero nuevo control de fidelidad detecta 63 eventos con desviación angular >15°, hasta 85,0958°.
6. Se añadió comparación diferencial entre el editable `.blend` y GLB exportado (`bee66d84`, pendiente de resultado en el momento de este registro) para distinguir fallo de retarget respecto a fallo de exportación. No usar `run success` como aprobación G1.
7. No hubo publicación de assets comerciales ni modificaciones de Anvil Fitness/Supabase.

### Verificación visual de la iteración G1.4 — 2026-11-18

- Se descargó realmente el ZIP de CI #14404254672 y se verificó su contenido (GLB, .blend, 2 WebP de ocho fotogramas y PNG/manifest).
- Se montaron 16 fotogramas de los WebP y se inspeccionaron junto con el render de reposo; fallan anatomía, amplitud articular y coherencia espacial. El resultado cuantitativo de 85° de error de rodilla tiene evidencia visual directa.
- Diagnóstico diferencial: el reposo GLB corregido es coherente. Prioridad de reparación: sistema de transformación y jerarquía de retarget, luego IK y apoyos; no ocultar defectos con smoothing ni aprobar export comercial.

## G1.5 — 2026-11-18 — el error de fase glTF era QA, no pérdida de animación; review queue real
1. Se cambió el retarget de `posebone.matrix` (matriz armature global con traducciones implícitas) a swing local quaternion con la jerarquía evaluada en la rama PR #16. Test real GLB: 53 bones, 16 dirigidos, separación de articulaciones <=0,5 micras y traslación no-root <=0,2 micras.
2. Primera revisión E2E detectó diferencial de flexión aparente >60° entre .blend/GLB. El test comparaba índice 6 FPS del .blend en el GLB importado a 24 FPS. Se corrigió la cadencia, revelando después error de apoyo 5 cm. 
3. Se descargó y leyó el GLB real en binario: los 160 canales glTF contienen timestamps con inicio 0,166667 s (`frame=1` del original). Se corrigió la conversión de tiempo en el test, eliminando +1 frame extra. No se relajaron tolerancias.
4. [CI 44266045114](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44266045114) SUCCESS técnico dual: diferencia angular .blend→GLB 0,0000° masculino/0,0001° femenino; apoyo vertical max 0,0000006/0,0000011 m. **El movimiento fuente sigue rechazado visualmente** y tiene 3 eventos de error rodilla por avatar >15°, max 23,4815°; sin IG/IK, root absoluto, colisiones ni contactos confirmados.
5. Se implementó `ems review-queue` en PR #23 con hash cruzado de vídeo/modelo/solved/artifacts, identidad de avatar, licencia y SHA del archivo de atribución. La cola guarda eventos medidos, evita duplicados y rechaza sobrescritura de un resultado distinto. No eleva derechos. [CI con artefactos REALES 44267734880](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44267734880) PASS: generadas **18 incidencias**, estado `REVIEW_REQUIRED`, distribución `BLOCKED`.
6. Los 8 fotogramas PNG/WebP inspeccionados por sexo siguen mostrando cuerpos torcidos/inverosímiles; el problema restante ya no es exportación glTF sino reconstrucción/retarget biomecánico. No fusionar PR #16.
