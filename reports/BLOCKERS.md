# Bloqueos y dependencias externas

| ID | Estado | Necesidad | Desbloqueo |
|---|---|---|---|
| B-01 | OPEN | Clips reales autorizados para T01–T10 | Aportar 10 MP4 o referencias con permiso documentado |
| B-02 | PARTIAL | Dos humanos MPFB CC0 generados con 53 huesos y deformación verificada en CI; faltan derechos de empaquetado/apariencia y QA de distribución | Completar revisión legal y visual y retarget real |
| B-03 | OPEN | Modelos y perfiles cinemáticos de polea y prensa | Construir/buscar modelos autorizados y validar mecánica |
| B-04 | OPEN | Validación en equipo Windows con Blender y herramientas instaladas | Ejecución y evidencias en el host objetivo |
| B-05 | OPEN | Integración con Anvil/Supabase | Requiere autorización separada y plan de rollback |

Continuar tareas independientes; no convertir un bloqueo en PASS.
| B-06 | PARTIAL | Modelo Full v1 de MediaPipe con SHA fijado y licencia Apache-2.0 afirmada por Google; resta auditar obligaciones de empaquetado y notice Windows | Incorporar licencia/notices al paquete final y revisar dependencias transitivas antes de explotación |
| B-07 | PARTIAL | Pose real 46/47 frames y GLB diagnóstico animado probados; sin clip canónico, retarget 2 avatares ni GLB final | Implementar solver de articulaciones, normalización, rig y QA biomecánica sobre T01–T03 |
| B-08 | OPEN | Inspección humana de asset y pruebas con dos rigs; el nuevo modelo no cuenta como comercial APPROVED | Revisar render/GLB, autorizar origen y probar manos/agarre con ambos avatares |
| B-09 | OPEN | Falta almacenamiento permanente del asset y catálogo completo | Definir artefactos versionados para activos aprobados, generar resto de familias y cubrir Kinetic |
| B-10 | PARTIAL | Dos avatares MPFB técnicamente riggeados (CI 44117210502), sin animación de vídeo ni QA humana | Retarget del solved_skeleton real, IK, calidad visual y licencias definitivas |
| B-11 | OPEN | Captura verificada sólo sobre un vídeo real de sentadilla unilateral CC BY-SA 4.0; no existe matriz T01–T10 aprobada | Incorporar diez vídeos propios/autorizados y revisiones de imagen, biomecánica y licencias |
| B-12 | OPEN | Versión MediaPipe 0.10.35 y FFmpeg probadas en Ubuntu; instalación final Windows x64 no ensayada | Test Windows real, fijar librerías nativas y licencias/NOTICE del instalador |

| B-13 | OPEN | En el clip real, desviación segmental original máxima 44,1919 %, 86 segmentos de baja visibilidad y cinco cambios angulares >450°/s; imporponer longitudes constantes no corrige profundidad, ruido ni contacto | Implementar filtrado temporal con QA, calibración, análisis biomecánico y revisión visual; no convertir estos outliers en PASS |
| B-14 | OPEN | Existe un esqueleto intermedio con dos GLB técnicos, pero no dos avatares humanos riggeados de calidad comercial | Integrar generador/modelos fuente CC0 con skinning, materiales y rig normalizado, demostrar retarget visual sobre ambos |

| B-15 | OPEN | La barra olímpica 20/60 kg es solo un activo procedural estático, sin movimiento acoplado a dos manos ni validación con ambos avatares | Ejecutar T06/T07 real autorizado con rig, restricción bilateral, colisiones, glTF animado y QA |
| B-16 | OPEN | Ambos activos humanos y barra originales tienen revisión visual comercial y aprobación de distribución PENDING | Revisar evidencias CI temporales, guardar provenance y firmar aprobación previa a publicar |

| B-17 | OPEN / VISUAL_FAIL | Retarget sobre humano real deformable: GLB y vertex animation técnicamente PASS pero anatomía visual completamente inválida (caderas/piernas, torsiones, contacto) en CI 44120835127 y 44121806410 | Comparar bind-pose GLB vs .blend original, revisar poseBone.matrix jerárquico, deltas de referencia, pivotes y skinning; exigir fotogramas reproducibles y validación visual humana antes de merge G1 |
| B-18 | OPEN / LICENSE_REVIEW | Movimiento derivado del vídeo Wikimedia CC BY-SA 4.0: resultados diagnósticos deben cumplir atribución y condiciones ShareAlike, incompatibles con distribución exclusiva propietaria sin estudio | Mantener únicamente como QA y usar vídeo propio/autorizado para clips distribuibles exclusivos; auditar licencias por recurso |
| B-19 | FIXED | Inversión del parámetro `gender` MakeHuman en artefactos iniciales AG1 | PR #15 fusionada y CI 44118646868: `male=1.0` / `female=0.0` conforme a macro.json pinned; descartar artifacts anteriores |

| B-17-FIX-A | FIXED | La geometría auxiliar MakeHuman Mask se exportaba a GLB como falda/piezas extra, provocando enormes artefactos antes del retarget | PR #18 main 68288f2 y CI 44124085638: export_apply=True, comparación geométrica bind-rest máxima 0,0000007 m |
| B-20 | OPEN / VISUAL_FAIL | Tras corregir el bind-rest (GLB exacto), las animaciones humanas del vídeo monocular siguen con movimientos no anatómicos y penetraciones en algunos frames. El QA de malla animada pasa indebidamente como proxy de calidad | Reforzar swing relativo, orientación local jerárquica, calibración, oclusiones, velocidad angular, root y controles de IK/contacto; fijar thresholds visuales y biomecánicos y añadir ejercicio real menos ocluido |

| B-21 | OPEN / KINEMATIC_FAIL | Retarget humano de la PR #16: test independiente contra el vídeo real mide 63 pares >15° y 85,0958° de error máximo en flexión de rodilla pese a CI E2E técnico verde | Aislar error en Blender editable frente a GLB, reparar jerarquía/rotaciones/oclusiones y repetir matriz con revisión frontal/lateral/3-4 |
| B-22 | OPEN / SUPPORT_LIMITATION | Anclaje vertical de pies aprobado técnicamente (1,59 cm de discrepancia GLB), pero no representa contacto real 3D ni corrige deslizamiento horizontal ni penetración | Implementar soporte/IK de pies, contactos temporales y validación de deriva XY antes de G1 |

| B-23 | OPEN / VISUAL_FAIL | 8 fotogramas por sexo del artifact 14404254672 revisados: hombros/torso y piernas presentan deformaciones severas, pese a avatar GLB válido en reposo y al anclaje Z técnico PASS | Corregir orientaciones locales/jerarquía del retarget con comparación GLB frente a .blend y repetir vistas frontal, lateral y 3/4 antes de integrar PR #16 |
