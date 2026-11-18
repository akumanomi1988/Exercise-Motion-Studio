# Banco regulable original — iteración AG2

**Estado:** implementación de geometría y cinemática en evaluación técnica. **NO es un activo comercial aprobado** ni prueba la interacción con un avatar.

## Arquitectura

- Generador: `src/blender/generate_adjustable_bench.py`, geometría original creada con primitivas Blender, sin modelos externos.
- Variantes permitidas: 0°, 30°, 45°, 60° y 75°. Los tests E2E generan 0°, 45° y 75° (no confundir tres ejemplos con cobertura completa de modelos de banco).
- Respaldo: malla articulada alrededor de la bisagra de posición `(0,-0.18,0.50)` metros, eje X, límites de diseño 0°–75°.
- Soporte: dos elementos telescópicos de carcasa/varilla por lado, con acoplamiento geométrico al respaldo. Las transformaciones se recalculan desde dos extremos a cada fotograma, sin física de cargas.
- Asiento fijo y respaldo tienen superficie de contacto y colisionador de tipo caja orientada. La malla no emplea marcas ni diseños propietarios.
- Escena editable `asset.blend`, `asset.glb` con animación de **ajuste del respaldo**, `preview.png` y `asset.json`. La animación es una comprobación mecánica; **no representa un ejercicio físico capturado**.
- Prototipo sin simulación estructural, validación de carga, contacto con humano, interacción mano/asiento o certificación de equipamiento real.

## Construcción reproducible

```bash
for angle in 0 45 75; do
  blender -b --factory-startup --python-exit-code 10 \
    --python src/blender/generate_adjustable_bench.py -- \
    --output-dir "data/generated_assets/bench-${angle}deg" --back-angle-deg "$angle"
  blender -b --factory-startup --python-exit-code 10 \
    --python tests/asset/qa_adjustable_bench.py -- \
    --asset-dir "data/generated_assets/bench-${angle}deg"
done
PYTHONPATH=src/motion_pipeline python -m unittest discover -s tests/unit -v
PYTHONPATH=src/motion_pipeline python -m ems asset-check --asset-dir data/generated_assets/bench-45deg
# Debe rechazar la distribución sin revisión:
PYTHONPATH=src/motion_pipeline python -m ems asset-check --asset-dir data/generated_assets/bench-45deg --require-commercial
```

En Windows, ejecutar los mismos comandos desde PowerShell ajustando el bucle y `$env:PYTHONPATH`.

## QA y gates

`qa_adjustable_bench.py` comprueba en Blender real: 19 mallas fuente, número de mallas/materiales GLB tras reimportación, archivo editable, movimientos a cinco fotogramas, límites de articulación, coincidencia de pivote, extremos de cuatro piezas telescópicas, discrepancia angular entre `.blend` y GLB, PNG no uniforme y hashes de integridad. Los casos unitarios del catálogo verifican cajas orientadas, quaternions normalizados y dimensiones positivas.

- `AG2` continúa **IN_PROGRESS**, `G2` **NOT_STARTED**: faltan banco plano/declinado/Scott, agarres, contacto/avatar, visual comercial, múltiples máquinas/equipos.
- `G1` continúa **IN_PROGRESS / VISUAL_FAIL** en la PR #16; este activo no cambia el estado del retarget.
- Derechos de geometría procedural: generado internamente, auditoría de propiedad/distribución **PENDING** hasta revisión documentada.
- Faltan prueba con avatar masculino/femenino, pie/suelo, contacto con asiento/respaldo, funcionamiento de GLB en Three.js y certificación mecánica (si alguna vez se presenta como equipo fabricable).

## Publicación

La CI genera archivos técnicos temporales como artefactos, no como distribución pública comercial. No se exportará a Anvil Fitness ni a Supabase. Mantener la PR en borrador mientras los tests o el QA visual fallen.

## Evidencia de ejecución real — 18/11/2026
- El exportador glTF debe usar `export_animation_mode="ACTIVE_ACTIONS"`, no el modo ACTIONS que separaba respaldos y telescopios y producía un modelo con articulaciones desincronizadas.
- CI real PASS: https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44276091657, Artifact 14414960823 (efímero). Avatares no incluidos en esta prueba.
- Un archivo `asset.glb` contiene **una** única animación y **13** canales; las cinco partes obligatorias están animadas juntas. Comprobado leyendo el JSON incrustado en el binario GLB, además de reimportar 0/45/75° y comparar .blend en cinco tiempos. Error angular 0°, error extremo <= 0,00001m.
- Las imágenes PNG renderizadas de las tres variantes se inspeccionaron y muestran una banqueta reconocible, aún técnica. No califican como render comercial aprobado ni comprueban humano/contactos, fuerza, carga o un ejercicio real.
