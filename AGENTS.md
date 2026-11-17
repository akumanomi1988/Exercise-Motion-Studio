# Instrucciones de ejecución — Exercise Motion Studio

**Documento normativo:** leer de principio a fin `ESPECIFICACION_MOCAP_3D_COMERCIAL.md` antes de modificar código. Si este archivo resume un requisito de forma ambigua, prevalece la especificación completa.

## Objetivo

Implementar un sistema **real**, local para Windows, sin Docker y apto para explotación comercial que, a partir de vídeos autorizados de ejercicios, capture movimiento humano, transfiera animaciones a avatares con rig propio, sincronice mancuernas/barras/bancos y máquinas con modelos 3D autorizados, y exporte GLB + WebP + PNG + `motion.json` + trazabilidad de licencias y QA. Preparar sustituir la representación visual de los ejercicios de Kinetic sin modificar Anvil Fitness hasta autorización.

## Orden estricto de prioridades

1. Licencias, derechos y seguridad.
2. Movimiento anatómicamente plausible y contactos correctos.
3. Funcionalidad real end-to-end sin mocks.
4. Pruebas, evidencia y reproducibilidad.
5. Calidad visual, UX y automatización.

## Prohibiciones

- No descargar ni procesar arbitrariamente vídeos ajenos de YouTube sin autorización; una URL es referencia, no prueba de derechos.
- No incluir assets, pesos, vídeos, clips o rigs `non-commercial`, sin licencia verificada, editorial only o con condiciones incompatibles con su redistribución.
- No usar Docker ni imponer GPU como requisito de la ruta base.
- No modificar Supabase, Anvil Fitness, ramas protegidas o YouTube sin autorización explícita.
- No mezclar Kinetic con otras bases de datos ni renombrar la aplicación durante este proyecto.
- No declarar éxito porque Python devuelve exit code 0, porque el GLB existe o porque los unit tests pasan: también deben pasar render, reproducción, biomecánica, materiales, licencias y revisión requerida.
- No relajar umbrales ni convertir fallos en warnings para declarar PASS.
- No presentar un movimiento procedural de emergencia como capturado de vídeo.

## Inicio obligatorio

1. Inspeccionar el repositorio y equipos instalados.
2. Auditar y fijar por commit los repositorios de referencia, paquetes, pesos y assets.
3. Crear estructura, contratos, fixtures legales, comandos setup/doctor/test, reportes y controles de permisos.
4. Implementar G0 y seguir I1… I6 del documento maestro.

## Tests

El piloto obligatorio consta de **10 ejercicios reales autorizados:** sentadilla, flexiones, zancadas, curl con una mancuerna, curl con dos mancuernas, press banca con barra, peso muerto con barra, remo apoyado, jalón al pecho y prensa. El objetivo de catálogo es **100 % de los ejercicios del snapshot validado de Kinetic**, con ID exacto, GLB, WebP, PNG, procedencia y QA aprobado. Los assets de maquinaria compleja precisan perfiles cinemáticos y revisión humana hasta demostrar validación automatizada equivalente.

### Gates

- **G0** ambiente limpio + auditoría + CLI + unit tests.
- **G1** T01–T03, rig, retarget a dos avatares, GLB, PNG, WebP.
- **G2** T04–T08, equipamiento libre y agarres correctos.
- **G3** T09–T10, máquinas con cinemática y revisión.
- **G4** piloto 10/10 con E2E y QA visual PASS.
- **G5** inventario Kinetic importado íntegro en staging, sin tocar Anvil.
- **G6** 100 % del snapshot Kinetic aprobado con medios finales reales.
- **G7** integración Supabase SOLO si la autoriza el usuario (dry-run primero).

No declarar `MVP_COMPLETADO` si algún G0–G4 falla. No declarar `CATALOGO_KINETIC_COMPLETADO` si algún G0–G6 falla. Los bloqueos externos no se transforman en PASS.

## Bucle de ejecución iterativa

```text
MIENTRAS exista una tarea accionable que avance el siguiente gate:
  1. Selecciona un requisito verificable y registra qué falta.
  2. Implementa el incremento más pequeño que dé resultado observable.
  3. Ejecuta pruebas unitarias, integración y E2E relevantes.
  4. Renderiza y verifica previsualizaciones de animación donde aplique.
  5. Verifica licencias/procedencia de cualquier material incorporado.
  6. Ante fallo: reproduce -> diagnostica -> repara -> reejecuta -> compara.
  7. Tras tres intentos sin progreso, cambia hipótesis o reduce a fixture mínimo.
  8. Documenta comando, salida, artefactos, hash, versión y estado de gate.
  9. Continúa con tareas independientes si una depende de permisos/revisión.
AL CERRAR LA EJECUCIÓN:
  Entrega estado comprobable (PASS/FAIL/BLOCKED), artefactos, próximos pasos.
```

Si falta un vídeo autorizado, avatar redistribuible, permiso, modelo de máquina o revisión humana, marca sólo ese ítem `BLOCKED` con solicitud concreta y continúa con otros. No afirmes que seguirás trabajando en segundo plano salvo que el entorno disponga realmente de una automatización persistente configurada.

## Archivos de auditoría obligatorios

Actualizar en cada iteración:

- `reports/IMPLEMENTATION_STATUS.md` — criterios y gates con PASS/FAIL/BLOCKED, commit, fecha, evidencia.
- `reports/ITERATION_LOG.md` — hipótesis, cambios, fallos y correcciones.
- `reports/TEST_RESULTS.md` — comandos, salidas reales, capturas, métricas.
- `reports/BLOCKERS.md` — impedimentos reales y acción requerida.
- `reports/LICENSE_AUDIT.csv` — cada dependencia, peso, vídeo y asset, origen/licencia/permisos.

**Primer comando de la primera sesión:** abrir la especificación y empezar I0/G0. No invertir toda la sesión en planificación sin crear y comprobar código ejecutable.

## Ampliación obligatoria — catálogo de activos 3D (AG0–AG5)

Leer **`docs/ASSET_LIBRARY.md`** como parte normativa del proyecto, junto a la especificación original. Implementar un catálogo reutilizable y versionado de **dos avatares (hombre y mujer) con rig**, pesos libres, mancuernas, discos, barras, bancos, racks, poleas, agarres intercambiables, bandas, accesorios y máquinas de gimnasio con cinemática funcional. Cada asset exige `asset.json`, source editable, GLB comercialmente distribuible, procedencia/licencia, preview y QA. La taxonomía del catálogo se reconciliará con todos los equipos usados por el snapshot de Kinetic. No marcar G2/G3/G4/G6 en PASS si faltan equipos, rigs, licencias o pruebas reales. Los gates AG0–AG5 y validaciones específicas están en `docs/ASSET_LIBRARY.md`.

Para iniciar una nueva conversación, puede emplearse `docs/PROMPT_CONTINUACION.md`; el estado efectivo debe consultarse siempre desde el repositorio, sus issues y los informes, no deducirse del prompt.
