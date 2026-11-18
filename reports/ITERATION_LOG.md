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

## G1.6 — 2026-11-18 — distribución parcial de torso/cabeza, sin aprobación de QA
- En PR #16 se modificó el motor Blender experimental: rotación del tronco distribuida 1/3, 1/2 remanente, 1/1 remanente entre `spine_01`, `spine_02`, `spine_03`, y cuello ligado a torso en lugar de dirección pecho→nariz no anatómica.
- CI real 44268989160 SUCCESS técnico (GLB, .blend, PNG, WebP ambos avatares); comparaciones de pie <=1,1 micras. 8 imágenes por sexo revisadas visualmente. Resultado `VISUAL_FAIL`: siguen miembros distorsionados, pelvis y extremidades imposibles, sin pole/IK ni contactos consistentes. No fusionar PR #16, pasada a borrador. Próximo requisito: IK bilateral y plano de flexión de codo/rodilla validado con vídeo real.
## 2026-11-18 — AG2: primera máquina simple articulada; corrección basada en E2E
1. Leídos AGENTS, especificación, taxonomía, arquitectura, derechos, 5 reportes y PR #16. La transferencia humana de vídeo real sigue VISUAL_FAIL: no fusionarla a main aunque el glTF sea técnicamente fiel. Se eligió el trabajo independiente AG2 banco regulable.
2. PR #25: código procedural Blender, 19 partes, asiento/respaldo, bisagra X, cinemática de 4 componentes telescópicos, 49 keyframes de ajuste, 5 posiciones de respaldos admitidas. Configuradas variantes 0/45/75° en E2E headless. Se añadieron colisionadores box orientados con tests de integridad y derechos comerciales fail-closed.
3. Python Actions #44274613992 PASS. Blender Actions #44274614075: las tres variantes **generaron .blend/GLB/PNG reales**, pero error QA en reimport: `L: telescoping rod detached from backrest`; no aprobar asset.
4. Sustituidas comparaciones de ejes locales por verificación geométrica de cilindros en coordenadas mundiales en test; nueva CI #44275032425 sigue FAIL a frame 13 por desviación radial de 0,05577 m. El error no es el mero test de origen local, por tanto se conserva como bloqueo real.
5. Añadidos diagnósticos cuantitativos sobre geometría y animación importadas, commit 997bf044. Próxima acción: inspeccionar Action CI, localizar fallo de reconstrucción/retiming de cilindros GLB, corregir exportador o transformación, reejecutar y registrar métricas. No rebajar tolerancias ni pasar a estado comercial.

### Resolución AG2.1 — 2026-11-18
6. El diagnóstico de GLB `a8025294` mostró que a frame 13 la posición/rotación del telescopio izquierdo correspondían al primer fotograma, mientras el respaldo sí avanzaba. La exportación por defecto `ACTIONS` dejó acciones inconexas. Cambiado a `ACTIVE_ACTIONS`, que fusiona las transformaciones activas en un único clip glTF.
7. CI Blender #44275823301 PASS de tres modelos: soportes coherentes a 5 instantes, precisión angular 0,0° y error extremo máximo 0,00001 m. Añadido parser de chunk JSON real GLB para rechazar múltiples clips o piezas sin animación; CI #44276091657 PASS con 1 animación, 13 canales, 5 piezas requeridas. Python #44276091655 PASS.
8. Descargado ZIP real 14414960823, inspeccionado `qa_report.json` de las tres variantes e imágenes PNG renderizadas. Geometría reconocible, simplificada, **no es resultado final comercial**. Mantener pendiente el contraste con humano y la firma de derechos.

## AG1.2 — 2026-11-18 — humanos originales Rocketbox en vez de figuras deformadas
1. Rechazados visualmente los avatares/animations de anteriores pruebas. Se seleccionó biblioteca Microsoft Rocketbox (MIT con assets originales incluidos), commit fijado `0943055d`, macho Sports_Male_01 y hembra Sports_Female_02 por ropa deportiva adecuada.
2. Descarga reproducible de FBX original, normales/colores y licencia mediante Git blob SHA1 y SHA256; un hash copiado sin nibble femenino disparó error fail-closed, corregido, sin desactivar controles.
3. Importador viejo FBX roto en Blender 5.0.1 (`ImportFBX.files`): sustituido por `bpy.ops.wm.fbx_import`. Ambos humanos auténticos llegan a .blend/GLB/PNG con 80 bones.
4. El análisis de GLB binario demostró cuatro texturas originales embebidas a 2048², pero el QA `bpy.data.images.has_data` reportaba falso negativo por carga diferida: sustituidas las comprobaciones por lectura de chunk PNG y resolución dentro de GLB binario; por tanto no se relajó el requisito de texturas.
5. La femenina contenía ruta TGA ausente para pelo/cutout: se añadió textura `f013_opacity_color.tga` original Git-pinned y se reconstruyeron los materiales usados con nodos PBR sin enlaces absolutos rotos del FBX; render sin artefactos magenta/púrpura.
6. Se evitó confundir materiales `Material` y `Dots Stroke` residuales de Blender con materiales reales de malla; se auditan solamente slots de las mallas. La comprobación de TGA decodificado en cache también dio falso negativo, sustituida por cabecera TGA real + validación posterior de PNG en GLB.
7. **CI 44296912327 SUCCESS** para los dos GLB, 80 bones, 25 mapeos, malla con skinning y deformación observada al girar brazos; **CI 44297081493 SUCCESS** tras copiar MIT íntegro a cada carpeta/asset, sin permitir publicación comercial. El vídeo real/retarget/IK continúa sin aprobar.

## 18/11/2026 — G1.7: migración real a Rocketbox, bug de tails glTF, QA y cola
1. Se auditó main `d1aec8e6`, PR16 original MPFB descartado para fusión por calidad visual, docs normativos y cinco reportes. Se creó rama `feat/g1-rocketbox-real-video-retarget-qa` y PR #27 draft. No Docker/Anvil/Supabase.
2. Se reutilizó el clip auténtico de Commons `Basic_single_leg_squat.webm` CC BY-SA 4.0 y SHA, Google MediaPipe Full y ambos avatares MIT SHA-pinned de `main`. Primer ciclo: 47 frames de captura, 46 detectados, 16 targets sobre rig 80 bones con .blend, GLB y 16 PNG. **CI #44301219987 falló** porque las cámaras quedaban vacías y el root Z llegó a ~14m. No se ocultó como PASS.
3. Diagnóstico instrumental en Blender `EMS_G1_RIG_SPACE_DIAG`: `rig.scale=(0.01,0.01,0.01)`, bones Blender importado con longitudes artificiales p.ej. `Bip01 Pelvis.length≈1202` unidades de armature, `Foot.tail` decenas de metros frente a malla de 1,8m. Sustituido `posebone.tail` por `posebone[child].head`, revisada conversión en metros y muestra de vértices evaluados en world-space. CI #44302626950 SUCCESS, máximos root 0,316/0,333 m; QA real de 188 fotogramas GLB (24fps) longitud segmento estable (relativo <0,000002).
4. Inspección humana de ocho frames/sexo en el artifact real: siluetas recuperadas y animadas, pero cámara en bind-rest recortaba piernas y calzado. Corrección medida: ajustar cámara a envolvente de malla `evaluated` sobre 8 frames auténticos y validar geometría contra clip-space del viewport (no solo PNG existente). CI #44303407819 SUCCESS y 16 capturas completas visibles.
5. Validación fuente→GLB detectó 141 ángulos codo/rodilla por sexo y **tres fallos izquierdos >15°**, máximo 23,603°. El error aparece también en fuente editable .blend; exportar no lo causa (drift GLB~0,001°). No se ajustaron umbrales ni se marcó G1 pass. Observaciones de fuente oculta y cambios bruscos requieren algoritmo temporal/IK robusto.
6. Se añadió cola ya existente `ems review-queue` a la nueva CI con contrato de articulaciones Rocketbox, hashes de MIT original y CC BY-SA, eventos de revisión deterministas. Tres tests unitarios de rechazo por derecho alterado, deriva segmento y bloqueo de aprobación. La aprobación G1/G4 y los medios comerciales siguen **BLOQUEADOS**.

## G5.1 — 2026-11-18 — primer inventario Kinetic real independiente
- Se verificó la rama oficial de `kinetic-place/exercises-db`, `main=75d59701...`, licencia MIT del fichero LICENSE real `e21da3a0...` y los Git blob SHAs de los dos JSON españoles completos.
- Nuevo módulo `ems.kinetic` y CLI `kinetic-audit`: carga sólo inputs locales con checksum contra upstream, mantiene 908 UUID de ejercicio, 44 UUID de equipo, identifica 1.086 asociaciones y backlog 44 tipos no vinculados a assets finales, sin incorporar YouTube/RepDB/media. Guarda fuente, SHA-256 y MIT en índice; rehúsa sobrescrituras distintas.
- E2E real GitHub CI 44364445904 SUCCESS y 6 unit PASS; se extrajo ZIP y se contrastaron las 16 familias, top por uso y once tipos no referenciados. No mezcla Anvil Fitness, storage externo ni vídeos de terceros.
- Siguiente: mapping exacto tipo+variante+agarre, generación procedimental y QA individual, contratos de export para 908 IDs. El snapshot solo acredita G5 parcial, nunca cobertura G6.

## G1.8 — 2026-11-18 — observación de apoyo, no contacto físico
1. Se auditó el nuevo main Rocketbox `ed3b0c05e` y se partió de su retarget real, no del MPFB experimental anterior. Se implementó apoyo candidato en la pierna derecha por altura relativa de toes visibles, evitando copiar el `bone.tail` ficticio del importador FBX.
2. Hipótesis: una raíz fija mantiene las piernas flotando o cruzando suelo. Se calculó movimiento de raíz XYZ en metros usando un único toe visible como hipótesis de apoyo; solo 37 de 47 frames elegibles; missing/contacto alterno continúan sin lock. Se mantienen 86 observaciones segmentales de baja visibilidad.
3. [E2E real 44361977459 SUCCESS](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44361977459): dos GLB de humano Rocketbox 80 huesos, .blend, PNG y WebP reales; 37 toes fijados, deriva mundo XY <0,000008 m. No se afirma contacto medido desde cámara.
4. La compensación XYZ generó 4 eventos de velocidad de raíz >1,5m/s por avatar (max ~3,04m/s), señal inequívoca de incertidumbre. Se modificó `ems review-queue` para trazar estos 8 eventos y dos hipótesis no verificadas; la cola pasa de 18 a 28 bloqueos con salida comercial inhabilitada; tests unitarios nuevos y [CI real 44363274678 SUCCESS](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44363274678).
5. Se añadieron cámaras frontal, lateral, tres cuartos, que renderizan la **misma pose original** y verifican hashes/framing sin sustituir datos reales. [CI 44364717095 SUCCESS](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44364717095) más Python checks 44364717089. Se descargaron PNG/GLB/Blender originales y se inspeccionaron hojas de contacto. La estabilización de toe es técnica, pero posturas no están aprobadas como ejercicio correcto, con rodilla izquierda >23° discordante del input y sin IK/contacto real.
6. Se fusionó PR #28 en main (`cbca072f`). **No reducir umbrales, no distribuir activos CC BY-SA como exclusivos ni modificar Anvil Fitness**. Próximo paso: estimación fiable de apoyo/plano suelo y restricciones de pole-vector/IK; revisar segundo vídeo autorizado menos ambiguo.
