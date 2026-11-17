# Bloqueos y dependencias externas

| ID | Estado | Necesidad | Desbloqueo |
|---|---|---|---|
| B-01 | OPEN | Clips reales autorizados para T01–T10 | Aportar 10 MP4 o referencias con permiso documentado |
| B-02 | OPEN | Avatares rigged con derechos comerciales y de distribución | Crear propios o auditar CC0/otras licencias |
| B-03 | OPEN | Modelos y perfiles cinemáticos de polea y prensa | Construir/buscar modelos autorizados y validar mecánica |
| B-04 | OPEN | Validación en equipo Windows con Blender y herramientas instaladas | Ejecución y evidencias en el host objetivo |
| B-05 | OPEN | Integración con Anvil/Supabase | Requiere autorización separada y plan de rollback |

Continuar tareas independientes; no convertir un bloqueo en PASS.
| B-06 | PARTIAL | Modelo Full v1 de MediaPipe con SHA fijado y licencia Apache-2.0 afirmada por Google; resta auditar obligaciones de empaquetado y notice Windows | Incorporar licencia/notices al paquete final y revisar dependencias transitivas antes de explotación |
| B-07 | PARTIAL | Pose real 46/47 frames y GLB diagnóstico animado probados; sin clip canónico, retarget 2 avatares ni GLB final | Implementar solver de articulaciones, normalización, rig y QA biomecánica sobre T01–T03 |
| B-08 | OPEN | Inspección humana de asset y pruebas con dos rigs; el nuevo modelo no cuenta como comercial APPROVED | Revisar render/GLB, autorizar origen y probar manos/agarre con ambos avatares |
| B-09 | OPEN | Falta almacenamiento permanente del asset y catálogo completo | Definir artefactos versionados para activos aprobados, generar resto de familias y cubrir Kinetic |
| B-10 | OPEN | Necesita 2 avatares comerciales realmente modelados y riggeados; esqueleto de debug no cuenta | Crear/importar con derecho demostrado, verificar skinning, huesos semánticos y retarget sin recalcular pose |
| B-11 | OPEN | Captura verificada sólo sobre un vídeo real de sentadilla unilateral CC BY-SA 4.0; no existe matriz T01–T10 aprobada | Incorporar diez vídeos propios/autorizados y revisiones de imagen, biomecánica y licencias |
| B-12 | OPEN | Versión MediaPipe 0.10.35 y FFmpeg probadas en Ubuntu; instalación final Windows x64 no ensayada | Test Windows real, fijar librerías nativas y licencias/NOTICE del instalador |

| B-13 | OPEN | En el clip real, desviación segmental original máxima 44,1919 %, 86 segmentos de baja visibilidad y cinco cambios angulares >450°/s; imporponer longitudes constantes no corrige profundidad, ruido ni contacto | Implementar filtrado temporal con QA, calibración, análisis biomecánico y revisión visual; no convertir estos outliers en PASS |
| B-14 | OPEN | Existe un esqueleto intermedio con dos GLB técnicos, pero no dos avatares humanos riggeados de calidad comercial | Integrar generador/modelos fuente CC0 con skinning, materiales y rig normalizado, demostrar retarget visual sobre ambos |
