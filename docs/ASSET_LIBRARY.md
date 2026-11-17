# Biblioteca de activos 3D para gimnasio (REQUISITO OBLIGATORIO)

**Estado:** especificación; NO implica que ya existan modelos finales, validación visual ni permiso comercial. Documento complementario a `ESPECIFICACION_MOCAP_3D_COMERCIAL.md` y `AGENTS.md`.

## Objetivo
Construir un **catálogo extensible, reutilizable y comercialmente explotable** de avatares, pesos, barras, máquinas, poleas, agarres y accesorios. Una animación esquelética debe reproducirse sobre hombre y mujer y con sustitución parametrizada del equipamiento. El motor conserva IDs estables, no duplica geometría innecesariamente y permite ampliar el catálogo sin reescribir el pipeline.

## Entregables por activo
- Modelo fuente editable `.blend` y versión distribuible `.glb` (más exportaciones si se justifican).
- `asset.json` con ID estable, versión, `category/subcategory/variant`, unidad metros, escala, orientación, dimensiones, pivotes, materiales, LOD, colisionadores, restricciones cinemáticas, `attachment_points`, `grip_points`, `contact_surfaces`, procedencia, hash y licencia.
- Vista previa PNG, captura/render automatizado y pruebas de importación/exportación Blender/Three.js.
- Máquinas móviles: piezas, jerarquía, tipo de articulación, ejes, rangos, transmisión (cable/polea), límites y trayectorias; geometría estática sola NO se considera máquina animable.
- No distribuir ni aprobar un activo sin revisión documentada de sus derechos y QA.

## Avatares (mínimo obligatorio)
Dos avatares originales o válidamente autorizados, **hombre y mujer**, completamente modelados, texturizados y **riggeados** (armature + skinning + jerarquía semántica), disponibles para distribución comercial dentro de GLB y visualización pública. Blender source y GLB; cuerpos proporcionados, postura neutral T/A, retarget canónico, IK y restricciones de pies/manos, articulaciones y dedos funcionales cuando el agarre lo exija. LOD para WebGL móvil. Nunca usar simples rigid bodies para sustituir un rig. Los dos deben aprobar animación T01–T10 sin intersecciones relevantes y sin deslizamiento visible no justificado. Posible ampliación futura: tallas, morfologías, tonos de piel y ropa modular; sin imponer sexo como requisito al esqueleto.

## Taxonomía de gimnasio (cobertura mínima que debe auditarse y ampliarse)
1. **Peso libre:** mancuerna hexagonal/ajustable/redonda, barra olímpica corta/larga, barra EZ/Z, trap/hex, barra técnica, barras fijas, barra safety squat, barra suiza, discos estándar/fraccionales, collars, kettlebell, landmine, slam/medicine ball, sandbag.
2. **Bancos y soportes:** plano, regulable/inclinado/declinado, banco predicador Scott, lumbar/hiperextensiones, banco abdominal, rack/squat rack/power rack, Smith, soportes para barras/mancuernas y cajones.
3. **Máquinas guiadas y selectorizadas:** prensa 45°/horizontal/vertical, hack squat, extensiones y curl femoral sentado/tumbado, aductor/abductor, gemelos sentado/de pie, jalón, remo sentado, pec deck/reverse fly, chest press horizontal/inclinado, shoulder press, dips asistidos, pull-up asistida, pullover, glute kickback, hip thrust, multipower y funcional equivalente. Crear familias paramétricas de máquinas, no una geometría única por nombre comercial.
4. **Poleas:** crossover doble, polea alta/media/baja, polea ajustable, torre individual, stack de placas, cables, poleas giratorias, pin y topes.
5. **Agarres intercambiables de polea:** barra recta corta/larga, barra lat ancha, barra curva/EZ, cuerda simple/doble, mango individual D, mango en V estrecho/neutro, barra paralela, MAG-like genérico (sin copiar marcas/diseños), mango tipo estribo, agarre supino/prono/neutral/ancho/estrecho, tobilleras, cinturón para polea y accesorios con mosquetón.
6. **Elásticos y suspensión:** banda loop corta/larga, mini-band, tubo con asas, banda asistida, anclaje de puerta/pared, suspensión con estribos, bandas de distintos niveles de resistencia.
7. **Calistenia y accesorios:** barra dominadas, paralelas, dip station, anillas, colchoneta, rueda abdominal, steps, cuerda de saltar, foam roller, balón de estabilidad/BOSU genérico, battle rope, trineo y arnés, escalera de agilidad.
8. **Cardio (inventario):** cinta, bicicleta estática/spinning, elíptica, remo, escaladora, air bike, ski erg. Modelado y cinemática según prioridad/uso real.
9. **Accesorios de seguridad y entorno:** cinturón de lastre, chaleco lastrado, straps, muñequeras, acolchados, pinzas, espejos, suelo y apoyo de cámara/iluminación.

**Cobertura real:** cruzar taxonomía con el snapshot fijado de Kinetic y cada uno de los equipos utilizados por sus ejercicios. No asumir que un listado genérico ya cubre todos; reportar IDs faltantes y variantes por familia. Evitar marcas, logos y diseños industriales protegidos cuando no exista permiso.

## Estrategia de obtención
Preferencia por **generación procedural original con Blender/Python** (geometría modular/paramétrica) para objetos y máquinas, y por avatares originales o modelos base con permisos de redistribución comprobados. CC0 auténtico es alternativa. Verificar licencias de base mesh, ropa, texturas, pesos de IA y rig, no sólo el código generador. No añadir Renderpeople, Mixamo u otros recursos con restricciones incompatibles como base por defecto; no inferir permiso comercial de que un repositorio sea MIT/Apache.

## Contratos entre componentes
- `AssetCatalog`: listado versionado y búsqueda tipada por clase/ID.
- `RigProfile`: mapa huesos, IK, proporciones y calibración por avatar.
- `EquipmentAsset`: geometría, dimensiones, masa opcional, agarres, sockets y colisiones.
- `MachineProfile`: árbol de partes, pivotes, juntas, límites, poleas/cable y desplazamiento.
- `ExerciseSceneDefinition`: ejercicio, rig, motionClip, equipo, posiciones, vínculos de contacto, cámara y bucle.
- `RenderPreset`: GLB/WebP/PNG/mobile; salida reproducible por hash.

## QA y aceptación
- Inspección en visor Three.js/Blender, comparativas frontal/lateral/3/4 y captura de resultados.
- Retarget animado sobre ambos avatares (no solo rig estático), penetraciones, contacto con banco/suelo, pies y manos. Para poleas y bandas, restricción de longitud/elástica y direcciones plausibles.
- Cada familia tiene un fixture mínimo animado y un asset renderizable; no permitir placeholders como PASS.
- Los tipos de equipamiento de Kinetic deben quedar asociados a IDs de catálogo aprobados; registrar las excepciones explícitas.
- Toda generación debe ser incremental, idempotente y sin reconstruir objetos idénticos; cache por hash y LOD.
- Aceptación de catálogo: `all_referenced_equipment_resolved == true`, `approved_avatar_count >= 2`, `missing_licenses == 0`, `qa_failed_assets == 0` y escenas piloto T01–T10 aprobadas; solo contar pruebas ejecutadas y evidencia real.
- No elevar G2/G3/G4/G6 a PASS con máquinas/avatares pendientes. Continuar por familias hasta cubrir el snapshot definido.

## Trabajo por fases (AG = Asset Gate)
- **AG0:** contrato de catálogo, validadores, schema, import/export y pruebas.
- **AG1:** avatares hombre/mujer, dos rigs y retarget real.
- **AG2:** peso libre, bancos y accesorios con agarre.
- **AG3:** poleas, agarres, bandas y accesorios flexibles.
- **AG4:** máquinas parametrizadas completas con articulaciones.
- **AG5:** inventario Kinetic 100 % vinculado a activos aprobados y compatible con animaciones por ejercicio.

Actualizar `reports/IMPLEMENTATION_STATUS.md`, `reports/LICENSE_AUDIT.csv` y `reports/TEST_RESULTS.md` en cada iteración. No declarar estas fases completas antes de las pruebas reales.
