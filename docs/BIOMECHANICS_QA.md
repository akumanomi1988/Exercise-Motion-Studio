# QA biomecánico y de escena

No declarar PASS por la existencia de `motion.json` o `exercise.glb`.

## Controles obligatorios
1. Datos finitos, FPS consistente, duración positiva y transformaciones válidas.
2. Rig animado real, >1 pose distinta, importación GLB de regreso y reproducción web.
3. Longitud de huesos canónicos estable (<1 % salvo ajuste documentado).
4. Detección de saltos, rotaciones imposibles, clipping y cámaras recortadas.
5. Apoyo de pies/manos estable; deriva objetivo <=3 cm en contacto confirmado (escena calibrada).
6. Agarre mano-equipo <=3 cm cuando se confirme; ambas manos en barra; objeto con escala y orientación constantes.
7. Máquina dentro de sus límites, articulaciones compatibles, sin penetraciones severas.
8. Inspección visual frontal, lateral y 3/4, y comparación con vídeo de referencia autorizado.
9. Evaluación independiente de calidad del movimiento, no sólo de la geometría o del encoder.
10. Licencias revisadas para CADA recurso incluido.

Esos umbrales son objetivos iniciales, no garantía clínica ni normativa universal. Ajustes específicos requieren evidencias y aprobación; no degradarlos para pasar pruebas.

## Resultado
`PASS`, `FAIL`, `REVIEW_REQUIRED`, `BLOCKED`. Solo un humano autorizado registra una revisión visual humana como aprobada. Fixtures sintéticos no sustituyen los 10 vídeos reales del piloto.