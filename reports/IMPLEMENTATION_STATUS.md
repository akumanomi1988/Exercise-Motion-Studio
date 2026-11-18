# Estado de implementación

Actualizado: 2026-11-17 — estado técnico tras PR #13 (merge `3ba87c7`) y PR #14 (CI `44117688418`).

**Resultado global: IN_PROGRESS — captura de pose 3D REAL implementada y probada; retargeting humanoide y catálogo NO completados.**

| Gate | Estado | Evidencia / Pendientes |
|---|---|---|
| G0: entorno limpio Windows, CLI, tests, auditoría | IN_PROGRESS | Registro + decodificación completa de vídeos mediante FFmpeg; Linux CI PASS 15/15 (run 44103138578). Falta Windows real/Blender/.NET, locks y auditoría de distribución |
| G1: movimiento, dos avatares, T01–T03 | IN_PROGRESS | Captura real 46/47 fotogramas, 33 landmarks 3D relativos y GLB diagnóstico animado. Hay esqueleto intermedio y dos avatares skinned verificados; faltan retarget real, contactos y T01–T03 con QA humano |
| G2: equipamiento libre T04–T08 | NOT_STARTED | Mancuerna hexagonal y barra olímpica procedural con discos verificadas técnicamente; sin contacto/IK ni aprobación comercial |
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

## I1.2 — solver de longitudes + dos GLB de diagnóstico (PR #12)

- Python CI [run 44113258264](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44113258264): **41/41 tests PASS**.
- E2E con humano real [run 44113258239](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44113258239): PASS técnico, mismo vídeo Commons legalmente atribuido, 47 muestras/46 detecciones; `solved_skeleton.json` generado a partir del `pose_raw.json` con identidad y SHA comprobados.
- Variación segmental original máxima **44,1919 %**; tras imponer longitudes estables desviación calculada **0 %** (propiedad geométrica, NO validación biomecánica). 86 muestras de segmento de baja visibilidad y cinco saltos de dirección sospechosos (máximo 504,908 grados/s) registrados para revisión.
- Dos GLB de diagnóstico generados y reimportados en Blender: original 51 objetos animados, intermedio con segmentos fijos 33 objetos animados; ambos con PNG y WebP animados de ocho fotogramas.
- **G0 y G1 continúan IN_PROGRESS**: falta validación Windows, calibración, biomecánica, retarget real a dos avatares con skinning y T01–T03. AG1 sigue NOT_STARTED. Ningún recurso de diagnóstico está aprobado para producción comercial.


## AG1.1 — 2 avatares humanos MakeHuman/MPFB, pruebas reales de Blender
- [PR #13 fusionada](https://github.com/akumanomi1988/Exercise-Motion-Studio/pull/13), commit main `3ba87c7`.
- [CI Blender SUCCESS 44117210502](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44117210502): hombre y mujer generados por separado; 19.158 vértices originales por avatar, 53 huesos con jerarquía común, skinning real y deformación de hueso verificada en el GLB reimportado. `.blend`, `.glb`, PNG y manifiestos creados en artifact 14344455745.
- MPFB fijado al commit `9de0707fdc88438d7c53a1a2ac7937d9221e2431`. Core/rig/weights CC0 según LICENSE upstream, plugin GPL usado como herramienta externa sin empaquetar. Revisiones legales completas de la cadena de distribución y apariencia humana todavía PENDING.
- **AG1 = IN_PROGRESS**: falta retarget desde vídeo real sobre ambos avatares, contactos, vídeo T01–T03, validación visual humana, licencia final, web viewer. No confundir prueba de deformación de rig con animación biomecánica válida.

## AG2.1 — barra olímpica procedural original, sin movimiento
- [PR #14](https://github.com/akumanomi1988/Exercise-Motion-Studio/pull/14), [CI Blender SUCCESS 44117688418](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44117688418): generador paramétrico de barra de 2,20 m, mangas, collars, discos anulares y dos sockets de agarre.
- Variantes reales generadas/reimportadas: 20 kg nominal (7 meshes, envelope 2,20 × 0,078 × 0,078 m) y 60 kg nominal (9 meshes, envelope 2,20 × 0,45 × 0,45 m). Archivo fuente Blender, GLB y PNG 960×480. AssetCatalog: integridad PASS y comercial `distribution_allowed=false`, como corresponde.
- Derechos, revisión de imágenes, IK de ambas manos y sincronización real con vídeo: PENDING. **AG2/G2 = IN_PROGRESS/NOT_STARTED según criterios de gate**. No representa un ejercicio exportable aprobado.

## AG1.2 — corrección morfológica y auditoría visual de retarget (2026-11-17)
- [PR #15 fusionada](https://github.com/akumanomi1988/Exercise-Motion-Studio/pull/15), `main=3d8ed55`: se corrigió la asignación invertida de parámetro `gender` de MakeHuman, confirmada con `macro.json` CC0. Antes de la corrección las etiquetas male/female de los gltf generados estaban intercambiadas; **descartar sus artefactos anteriores**. [CI corregida PASS 44118646868](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44118646868).
- [PR #16 experimental](https://github.com/akumanomi1988/Exercise-Motion-Studio/pull/16), **NO FUSIONAR SIN QA VISUAL**: procesó el vídeo real CC BY-SA de sentadilla a una pierna (46 de 47 fotogramas, MediaPipe), transfirió movimiento a 16 huesos por avatar, exportó dos GLB skinned animados, previews y WebP. [CI técnica PASS 44120835127](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44120835127); prueba de malla deformada real PASS.
- **Inspección visual humana del artefacto 14345087065 = FAIL.** Animaciones con penetraciones y deformaciones severas de piernas/caderas y cabeza. El QA técnico de GLB y malla deformada **no implica corrección biomecánica**.
- Iteración experimental posterior usa swing relativo a pose real de referencia + hold de observaciones ambiguas. [CI técnica 44121806410 SUCCESS](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44121806410), pero **inspección visual también FAIL**, con distorsión extrema del tren inferior. Se está diagnosticando por separado el bind-rest GLB y el retarget.
- Gate G1, AG1 y QA comercial siguen **NO APROBADOS**. No entregar estos dos GLB animados como ejercicios comerciales, ni incorporarlos a Anvil Fitness.

## AG1.3 — GLB bind-rest saneado, G1 vídeo real todavía rechazado (2026-11-17)
- [PR #18 fusionada](https://github.com/akumanomi1988/Exercise-Motion-Studio/pull/18), `main=68288f2`, [CI PASS 44124085638](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44124085638): `export_apply=True` elimina geometría auxiliar MakeHuman oculta mediante modificadores Mask; exportador conserva skin/53 huesos. GLB de 3,09 MB a 0,95 MB por avatar.
- Nueva regresión `qa_mpfb_bind_rest_fidelity.py` mide distancia en espacio mundial entre fuente .blend evaluada y GLB reimportado. Desviación P99 de 0,0000007 m y máxima de 0,0000007 m (ambas variantes): **PASS geometría y rig**. No implica aprobación comercial.
- [PR #16 sigue abierta](https://github.com/akumanomi1988/Exercise-Motion-Studio/pull/16), CI técnica [44124440610 SUCCESS](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44124440610), vuelve a generar ambos GLB animados sobre avatares ya saneados.
- **QA visual examinada del artifact 14346548007: FAIL.** Geometría de avatar corregida, pero poses/rotaciones monoculares violentas (sentadilla a una pierna) deforman cuerpo en determinados fotogramas. Fuente contiene cinco eventos de velocidad angular excesiva y oclusiones (antebrazo/codo derecho). La falta de twist, root, contacto/IK y robustez de extracción no está resuelta.
- G1 NO APROBADO. AG1: únicamente sub-gate de generación y fidelidad GLB técnica PASS; avatar de calidad comercial aún PENDING.

## G1.4 — 2026-11-18 — E2E con corrección vertical de apoyo (PR #16 NO fusionada)

- Rama experimental `feat/g1-real-video-dual-skinned-retarget`: commits `a94452bc` (raíz vertical basada en dedos del pie visibles) y `c7325aa3` (medición independiente tras GLB reimportado). Otros cambios concurrentes de flexión/twist se encuentran en la misma PR, no se consideran aprobados.
- [CI 44253263080](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44253263080) **SUCCESS técnico**: vídeo humano real Wikimedia (46/47 frames detectados), 2 GLB skinned de 53 huesos/16 mapeados, WebP animados y QA de soporte vertical. Error vertical GLB máximo 0,015859 m para los dos avatares (límite técnico 0,03 m).
- **FALLO biomecánico independiente:** 63 observaciones de articulación sobre 15°; error máximo de flexión 85,0958° y media 20,4285°. `kinematic_fidelity.status=FAIL_REVIEW_REQUIRED` en ambos avatares. Este CI verde NO certifica corrección de movimientos.
- G1 = **IN_PROGRESS / QA_FAILED**, AG1 = **IN_PROGRESS**, G2–G6 sin aprobación; licencias de outputs derivados CC BY-SA en revisión. Sin autorización comercial, sin `motion.json` final, sin T01–T03 completos, sin inspección visual de nuevos renders. **NO FUSIONAR PR #16** hasta superar control biomecánico y visual.

### G1.4 — inspección visual explícita de los previews (2026-11-18)

- La hoja de contacto se construyó extrayendo los 8 fotogramas reales de los WebP masculino y femenino del artifact **14404254672**, run **44253263080**. Se abrió también `retarget_male/imported_glb_rest.png` para separar defecto de bind-rest.
- **VISUAL FAIL**: torsión severa de tronco/hombros, piernas retorcidas y posiciones imposibles en varios fotogramas de ambos avatares. El GLB en reposo presenta anatomía normal; el defecto aparece con la animación. No es un problema exclusivamente de integridad del contenedor ni de geometría inicial.
- QA humana de producción continúa **PENDING**, y esta inspección técnica **rechaza expresamente** los renders actuales; mantener G1/AG1 **NO APROBADOS** y prohibida la publicación comercial.

## G1.5 — fidelidad del GLB y cola de revisión (2026-11-18)
- [PR #16](https://github.com/akumanomi1988/Exercise-Motion-Studio/pull/16) mantiene aislado el retarget de vídeo real, no fusionado por defectos visuales. Se sustituyeron matrices globales por swing quaternion local y se añadió QA de continuidad de huesos y traslación no-root; se corrigió la comparación de instantes 6 FPS (.blend) frente a 24 FPS (import glTF), incluyendo origen de claves glTF 0,166667 s.
- [CI E2E 44266045114 SUCCESS técnico](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44266045114), input CC BY-SA SHA `ab460282...`: ambos avatares .blend/GLB reimportados coinciden en ángulos a <=0,0001°, apoyo vertical error <=0,0000011 m, continuidad de articulaciones <=0,0000005 m. **Solo fidelidad de exportación, NO calidad biomecánica.**
- Datos de fuente muestran 3 errores de flexión de rodilla izquierda >15° por avatar, máximo **23,4815°**, 5 observaciones de velocidad angular anómala y 86 muestras de segmentos de baja visibilidad. Las imágenes reales de ambos WebP muestran torsiones/poses imposibles: **VISUAL FAIL**, G1 NO APROBADO.
- [PR #23](https://github.com/akumanomi1988/Exercise-Motion-Studio/pull/23) incorpora CLI local `ems review-queue`, fail-closed, con hashes cruzados de `solved_skeleton.json`, manifiestos, QA y atribución. [CI E2E real 44267734880 SUCCESS](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44267734880): 18 incidencias bloqueantes (6 flexiones de ambos avatares, 5 velocidades, 1 visibilidad, 2 visual, 2 derechos y 2 IK/contacto). `release_gate=BLOCKED`, `exercises_approved=0`.
- Sin máquinas adicionales aprobadas, sin licencia comercial de material derivado del vídeo y sin cambios de Anvil Fitness/Supabase. Próximo trabajo: resolver realismo anatómico (IK + postura bilateral/cara, estimación de profundidad y observaciones inestables), después ampliar piloto T01–T10; mantener PR #16 no fusionada hasta inspección visual REAL satisfactoria.

## G1.6 — torso swing distribuido y cuello conservador: VISUAL FAIL (2026-11-18)
- [PR #16](https://github.com/akumanomi1988/Exercise-Motion-Studio/pull/16) convertida a DRAFT para impedir aceptación prematura; run [44268989160](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44268989160) PASS técnico con los dos GLB reales y vídeo autorizado. Se reparte swing del torso en tres huesos `spine_01/02/03` en vez de concentrar todo en lumbar, y `neck_01` sigue la inclinación torácica porque nariz no define el eje del cuello.
- Inspección visual de 8 frames/sexo: cabeza más estable, **rodillas, caderas, brazos y torso aún con deformaciones imposibles**; el error de flexión de rodilla izquierda llega a 23,6026° frente al fuente. G1 permanece `VISUAL_FAIL/REVIEW_REQUIRED`, sin animación comercial aceptable. El resultado va a la cola real ya integrada en main mediante PR #23.
## Iteración AG2 — 2026-11-18 — banco regulable original (PR #25, revisión técnica en curso)
- Rama `feat/ag2-adjustable-bench-kinematic`, PR https://github.com/akumanomi1988/Exercise-Motion-Studio/pull/25 (DRAFT).
- Nuevo `src/blender/generate_adjustable_bench.py`: banco original con 19 mallas, asiento fijo, respaldo rotatorio articulado, eje/pivote y dos pares de soportes telescópicos; 0/30/45/60/75° parametrizados, salida editable .blend, GLB animado, PNG y asset.json con derechos PENDING.
- `src/motion_pipeline/ems/catalog.py` admite ahora colisionadores de caja orientada (además de cilindro) con normalización de cuaterniones; cuatro tests nuevos verifican rechazo seguro. CI Python 44274613992 y 44275032271 SUCCESS.
- Primera CI Blender https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44274614075 creó variantes 0/45/75° con Blender 5.0.1 pero QA GLB FAIL por desconexión de soporte telescópico importado. Rerun https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44275032425 FAIL: desviación radial GLB 0,05577 m en frame 13; nueva instrumentación commit 997bf044 para aislar causa sin reducir umbrales. **Estado del nuevo activo: FAIL_REVIEW_REQUIRED** hasta rerun verde y revisión visual.
- **G1 permanece IN_PROGRESS / VISUAL_FAIL** en la PR #16. **G2/AG2 no aprobados**: banco sin prueba de contacto/avatar, QA visual, revisión de derechos ni integración en ejercicios reales. No hubo cambios en Anvil Fitness o Supabase.

### Cierre técnico AG2.1 — 2026-11-18: GLB mecánico validado, NO comercial
- Causa aislada: el modo de exportación Blender glTF ACTIONS creaba clips separados por objeto; un visor/reimportación no activaba a la vez las barras telescópicas. Corregido explícitamente con `export_animation_mode="ACTIVE_ACTIONS"` en commit `7d6d94ce`.
- Real CI https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44276091657 **SUCCESS** (Blender 5.0.1), Python https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44276091655 **SUCCESS** (12/12 tests catalog). Tres variantes 0°, 45°, 75° generadas, comprobadas a cinco fotogramas por variante, 19 mallas originales/reimportadas, tolerancia mecánica/collider cumplida. **Una animación glTF de 13 canales anima juntas las cinco piezas móviles** en cada GLB. Drift ángulo = 0,0000° y drift extremo respaldo <=0,00001 m. Artefacto real 14414960823 (duración 7 días).
- Se descargó y revisó el archivo ZIP real y las previsualizaciones PNG (0°,45°,75°): banco funcional reconocible, acabado geométrico técnico, sin aprobación estética comercial ni validación de contacto con humano. La revisión no demuestra rig/IK, ergonomía, capacidad estructural ni que el activo sea comercializable. **AG2 IN_PROGRESS; G2 NOT_STARTED; licencia PENDING**.

## AG1.2 (18/11/2026) — riggeados Microsoft Rocketbox Sports, importados realmente
- **Candidatos hombre y mujer REALES** Sports_Male_01 y Sports_Female_02, Microsoft Rocketbox MIT `0943055d`; código de adquisición SHA-pin, conversor Blender y QA en PR #26.
- CI Blender 5.0.1 https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44297081493 **SUCCESS**, Python https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44297081549 **SUCCESS**.
- 80 huesos por avatar y 25 mappings semánticos compartidos, 4/5 texturas PNG embebidas a 2048², mallas skinned deformables, reimportación GLB PASS. Masculino alto 1,804148m, 4235 vértices con pesos tras reimport, 0,250412m deformación prueba de brazo. Femenino 1,737497m, 5433 vértices, 0,227177m deformación. Imágenes de reposo revisadas; se reparó transparencia del pelo.
- Texto MIT (c) 2020 Microsoft copiado a ambos paquetes. Hash contenido + procedencia a commit; `ems asset-check` PASS integridad, `--require-commercial` **rechaza** como corresponde. Generados .blend, .glb, PNG y reports sin vídeos de terceros.
- **AG1 IN_PROGRESS, G1 IN_PROGRESS/VISUAL_FAIL**: sin retarget a nuevo rig, sin locomoción/IK/contacto, sin visual de ejercicio real ni aprobación comercial; no cambiar G1 a PASS. El retarget experimental PR #16 queda aislado y no fusionado.

## G1.7 — 18/11/2026 — retargeting de vídeo REAL sobre dos avatares Microsoft Rocketbox (PR #27)
- **Aumento real implementado:** `src/blender/retarget_rocketbox_sports.py`, `tests/asset/qa_rocketbox_real_retarget.py`, encode WebP, CI independiente `rocketbox-retarget-ci.yml`, mapeo 16 huesos animados por rig de 80 huesos sobre Sports_Male_01 y Sports_Female_02 (MIT), sin reconstruir de cero los avatares ni tocar Anvil Fitness/Supabase. Vídeo humano original de RickyBennison CC BY-SA 4.0, SHA256 `ab4602823ad00de3409eb50d2c65c6b1ce5566c5dca6753555ff2b19107db88e` y modelo MediaPipe `5134a3aa...` fijados. Capture real 47 frames/46 detectados, no simulación.
- **Causa corregida en una prueba FAIL real:** primer E2E [44301219987](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44301219987) exportó animaciones pero corrigió la raíz ±14 m y renderizó fondos vacíos. Al importar Rocketbox GLB, Blender fabrica `bone.tail` para huesos procedentes de FBX con escala heredada 0,01; el hueso físico visible está entre **`bone.head` y `bone_hijo.head`**, no en el `tail` artificial. Reparados 16 targets, orientación, soporte toe, escala mundial de malla y los tests de cinemática.
- **Verificado Blender real:** CI [44302626950](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44302626950) SUCCESS, máximo root vertical **0,316 m hombre / 0,333 m mujer**, deformación auténtica 0,837/0,829 m, 80 huesos por GLB y 16 controlados, estabilidad de longitud anatómica <=0,000002 relativo, deriva de tiempo/ángulo Blender→GLB ~0,001°, toe vertical sobre referencia aproximada <=0,000013m (NO prueba de contacto físico con suelo).
- **Cámara arreglada:** un render inicial de la silueta dinámica cortaba piernas. `_fit_review_camera_to_actual_motion` mide los vértices evaluados de **ocho poses reales** por sexo, ajusta ortográfica; test independiente de viewport verifica cabeza, piernas y pies dentro en los ocho fotogramas. [CI 44303407819](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44303407819) SUCCESS con PNG reales, WebP animados y GLB para ambos.
- Se adaptó la cola fail-closed para valorar longitud entre heads, preservando hash de MIT Microsoft en cada avatar y fuente CC BY-SA del vídeo; `release_gate=BLOCKED`, `exercises_approved=0`.
- **G1 = IN_PROGRESS / BIOMECHANICS_VISUAL_FAIL**; 3 errores fuente→rodilla izquierda >15° por sexo, máximo **23,60°** en `2833 ms`. Hay 86 observaciones de baja confianza mantenidas, 14 clamps temporales; faltan IK, suelo XY, pole vectors, posturas anatómicas, validación humana frontal/lateral/3-4 y otros 9 vídeos piloto. **AG1 no se aprueba comercialmente.** Nuevos GLB derivados del vídeo CC BY-SA 4.0 solo QA; no afirmar que puedan publicarse como recurso propio exclusivo.

## G5.1 — snapshot Kinetic REAL fijado, sin media (2026-11-18)
- Snapshot oficial exclusivo `kinetic-place/exercises-db`, commit `75d59701c749243f522149d5edd63ec4c6870e5e`; `es/exercises.json` Git blob `ae8835aa...`, `es/equipment.json` `5b117cae...`. Licencia de los DATOS MIT copyright (c) 2026 Kinetic.place, archivada en el run. Las urls/media de YouTube externas NO están licenciadas por MIT de Kinetic y se excluyen.
- PR #29 implementa CLI offline `ems kinetic-audit`, hashes Git SHA-1 objeto y SHA-256 entrada, whitelisting sin vídeos/miniaturas ni RepDB, IDs de ejercicio/equipo intactos, control de integridad UUID/relaciones, salida atómica e idempotente; no escribe Anvil Fitness ni Supabase.
- [CI 44364445904 SUCCESS](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44364445904) usó ficheros completos originales, no fixtures: **908 ejercicios, 44 equipos, 1.086 asociaciones, 16 familias, 11 tipos de equipo sin ejercicio referenciador**. **44 de 44 equipos carecen de asociación a un asset 3D aprobado; 0 de 908 ejercicios aprobados.** Artifact 14455583095 con inventario metadata-only y LICENSE íntegra; unit tests 6/6 PASS.
- **G5 IN_PROGRESS**: inventario español reproducible, falta enlazar recursos y variantes reales/guías, QA y completar mapping de ejercicios; **G6 NOT_APPROVED**. En particular `Máquina` (72) y `Polea` (84) son categorías amplias, NO equivalen a una sola máquina/agarre funcional.
