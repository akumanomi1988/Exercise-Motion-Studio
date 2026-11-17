---
title: "Motor comercial de reconstrucción de ejercicios 3D"
subtitle: "Especificación funcional, técnica y protocolo de ejecución iterativa para agentes de desarrollo"
version: "1.0"
date: "2026-11-17"
status: "Especificación para implementación; producto aún no desarrollado"
---

# MOTOR DE EJERCICIOS 3D — ESPECIFICACIÓN MAESTRA

**Proyecto independiente:** `exercise-motion-studio`  
**Aplicación consumidora futura:** Anvil Fitness (sin rebranding ni modificaciones de su backend durante el desarrollo de este proyecto).  
**Objetivo:** transformar demostraciones de ejercicios en animaciones 3D originales, editables y comercialmente explotables, con movimiento corporal y equipamiento sincronizado, y preparar una sustitución verificable de la representación visual del catálogo Kinetic.  
**Prioridad:** legalidad comercial verificable > corrección biomecánica > integridad de activos > reproducibilidad > calidad visual > automatización > rendimiento.

> **Mandato de ejecución:** implementar, ejecutar, verificar, corregir y volver a ejecutar hasta cumplir los criterios de aceptación. No declarar `COMPLETADO` por haber generado archivos o por pasar pruebas unitarias si fallan la revisión visual, la sincronización del material, las licencias o los casos reales. Cuando falte un permiso, un vídeo accesible o una revisión humana imprescindible, detener solamente la tarea afectada con estado `BLOCKED`, evidencia y siguiente acción precisa; no inventar datos, permisos ni aprobaciones y no bloquear el resto de los trabajos independientes. El mandato de iteración exige trabajo efectivo en cada ejecución, no promesas de ejecución futura ni simulación de un proceso en segundo plano.

## 1. Resultado de negocio y alcance

El producto será una herramienta **local para Windows, sin Docker ni dependencia obligatoria de servicios cloud**, con interfaz para importar ejercicios, ver el progreso, inspeccionar resultados y exportar. Su núcleo será invocable también en modo CLI y por lotes para permitir automatización y pruebas CI.

Al recibir un vídeo de referencia autorizado de una persona realizando un ejercicio, el sistema deberá identificar su movimiento, construir una secuencia temporal de articulaciones, normalizarla en un esqueleto humanoide canónico, transferirla a uno o varios avatares nuestros, sincronizar utensilios o máquinas desde un catálogo 3D autorizado y producir animaciones verificables. La salida se utilizará después en una aplicación fitness comercial sin necesidad de alojar los vídeos originales.

### 1.1 Casos de uso

- **UC-01: ejercicio sin material.** Vídeo de sentadilla, zancada, flexión o dominada; avatar 3D reproduce el ciclo completo con pies y manos estables cuando corresponde.
- **UC-02: ejercicio con objetos libres.** Curl de bíceps con mancuernas, press con barra, kettlebell swing; objeto 3D propio sigue su trayectoria realista, con agarre y orientación coherentes.
- **UC-03: ejercicio con apoyo.** Press banca, remo apoyado, fondos, step; el cuerpo y el banco/plataforma respetan las superficies de contacto.
- **UC-04: ejercicio con máquina articulada.** Jalón de polea, extensión de cuádriceps, prensa de piernas; plantilla cinemática de la máquina con ejes, relaciones y límites, sin atravesar al usuario.
- **UC-05: variantes.** Reutilizar un movimiento canónico cuando sea biomecánicamente válido, ajustando agarre, amplitud, orientación y equipamiento, y señalando las variantes que requieren captura nueva.
- **UC-06: lote Kinetic.** Procesar el inventario importado y relacionar cada animación final con el ID del ejercicio, sin perder metadatos ni introducir ejercicios de otras bases de datos.
- **UC-07: reutilización del avatar.** Aplicar el mismo `motion.json` a un segundo personaje humanoide con proporciones diferentes sin reanalizar el vídeo.
- **UC-08: publicación.** Exportar un GLB con animación, una WebP animada, PNG de portada y manifiestos; preparar la importación posterior a Supabase Storage, sin publicar automáticamente activos sin aprobar.
- **UC-09: demostración en YouTube (opcional).** Mantener URL/vídeo propio como referencia editorial o demostración; ofrecer posteriormente reproducción oficial en la app, separada del motor de MoCap.

### 1.2 Fuera del alcance de la primera versión

- Garantizar reconstrucción automática fotorealista de **cualquier** máquina observada en un único vídeo.
- Recuperar medidas físicas absolutas, profundidades invisibles o biomecánica clínica exacta desde una sola cámara.
- Descargar masivamente vídeos ajenos de YouTube o neutralizar restricciones de acceso.
- Usar modelos 3D o pesos de IA con restricciones `non-commercial`, `research only`, `editorial only`, `no redistribution` incompatibles con el producto.
- Publicar automáticamente sobre `main`, en Supabase DEV/PROD o en YouTube sin permiso y sin las puertas de calidad.
- Convertir automáticamente un mesh estático o un conjunto de `Rigid Body` en humanoide articulado sin rigging.

## 2. Restricciones innegociables

**R-01, explotación comercial.** Todo componente distribuido y todo asset contenido en las salidas tendrá trazabilidad de licencia y uso comercial permitido: código, pesos de visión artificial, vídeo fuente, avatar, texturas, movimiento de terceros, máquinas, accesorios, fuentes tipográficas y audio. No inferir derechos de los activos desde la licencia del repositorio.

**R-02, origen del vídeo.** Aceptar MP4/MOV/WebM locales sobre los que exista base de uso documentada. Admitir URL de YouTube como referencia y metadato del propietario; si se desea procesar ese vídeo, el usuario facilitará un archivo fuente autorizado o una forma de obtención y procesamiento contractualmente permitida. No implementar descargas arbitrarias de vídeos de terceros como comportamiento por defecto. No confundir referencia visual con autorización para descarga y extracción masiva.

**R-03, no Docker.** Windows 10/11, instalación por PowerShell y entornos virtuales. Blender ejecutado en local/headless; CPU funcional y aceleración GPU opcional.

**R-04, aislamiento.** Repositorio propio y datos locales, sin tocar el proyecto Anvil Fitness hasta la aprobación del adaptador de importación. No mezclar Kinetic con RepDB u otras fuentes.

**R-05, reproducibilidad.** Dependencias bloqueadas por versión, hashes/commit SHA de repositorios externos, manifiestos por ejecución, logs estructurados y pruebas ejecutables desde cero.

**R-06, fidelidad.** Sin falsos éxitos: una captura 2D no equivale a rotaciones locales 3D correctas; un GLB válido no implica movimiento anatómico válido; un objeto localizado no implica agarre correcto.

**R-07, fallo seguro.** Si falta fuente legítima, rig compatible, maquinaria, calibración o fiabilidad suficiente, estado `REVIEW_REQUIRED` o `BLOCKED` según la causa. Nunca reemplazar silenciosamente la captura por una animación genérica y presentarla como clonada.

## 3. Stack recomendado y responsabilidades

| Capa | Implementación principal | Notas |
|---|---|---|
| Orquestador local | .NET 10, C#, procesos externos y JSON por `stdin/stdout` | Sin servidor HTTP obligatorio; CLI independiente |
| Interfaz de escritorio | WPF + WebView2 + React + TypeScript | Interfaz opcional tras estabilizar CLI; WebView2 bridge para jobs |
| Análisis de vídeo | Python 3.11, OpenCV, FFmpeg, NumPy, SciPy | Pinned y auditado; inicio CPU |
| Estimación corporal | MediaPipe Tasks Pose Landmarker | 33 landmarks y estimaciones 3D relativas; comprobar licencia de pesos concretos |
| Manos/agarres | MediaPipe Hand Landmarker o Holistic | Usar sólo cuando aporte a la detección de contacto |
| Motor de retarget | Adaptación evaluada de `s0ck3t/VideoIntoBlenderModel` | Apache 2.0 código; no incorporar automáticamente sus assets externos |
| Rig/escena/objetos | Blender 4.5 LTS o versión LTS estable verificada | Python `bpy`; jerarquía de bones, IK, constraints, exportación GLB |
| Generador y visor | Adaptación evaluada de `AssiamahS/opengym3d`, Three.js | MIT código; auditar cada asset y dependencia |
| Formatos | JSON/NPZ interno; GLB/glTF 2.0, PNG, WebP, MP4 opcional | `motion.json` es contrato propio versionado |
| Persistencia local | SQLite en host .NET + archivos por job | SQLite para estados, colas, hashes y trazabilidad |
| Integración futura | Exportación manifiesto + adaptador Supabase Storage | No escribir en Supabase por defecto |
| Pruebas | pytest, .NET tests, Vitest y Playwright | QA estructural + temporal + visual + humano |

**Decisión:** no usar motores de reconstrucción de cuerpo/objeto que dependan de pesos limitados a uso investigador sin obtener licencia comercial. El análisis monocular inicial será asequible en CPU; **la fase de objetos no se dará por resuelta con MediaPipe**, porque es un estimador de cuerpo/manos, no un reconstructor universal de maquinaria.

### 3.1 Hardware y requisitos de instalación

- **Mínimo de desarrollo:** Windows 10/11 x64; 16 GB RAM recomendados; CPU moderna; espacio suficiente para vídeos y Blender; Python, .NET SDK, Blender, FFmpeg y Git instalables sin privilegios especiales cuando sea posible.
- **GPU opcional:** NVIDIA con 8 GB VRAM permite experimentar con algunos pipelines, pero no garantiza ejecutar modelos grandes de visión/reconstrucción. La ruta CPU debe terminar al menos las pruebas de captura básica y exportación.
- **No exigir GPU en CI:** usar fixtures sintéticos de movimiento y renders pequeños en pruebas automatizadas.
- Incluir `scripts/setup-windows.ps1`, `scripts/doctor.ps1` y `scripts/test-all.ps1`; ejecución repetible e idempotente; PATH persistente sólo si es solicitado, verificado y sin sobrescribir entradas del usuario.

### 3.2 Repositorios candidatos

1. `https://github.com/s0ck3t/VideoIntoBlenderModel` — evaluar CLI, skeleton normalizado, retarget y compatibilidad real Windows/Blender. La integración debe ser mediante adaptador, no fork profundo prematuro.
2. `https://github.com/AssiamahS/opengym3d` — estudiar el pipeline Blender/GLB, controles visuales y los tests; **no** reutilizar indiscriminadamente avatares, clips Mixamo ni material de terceros.
3. `https://github.com/google-ai-edge/mediapipe` — plataforma de landmarks; comprobar también condiciones de los archivos `.task` específicos utilizados.
4. `https://github.com/kinetic-place/exercises-db` — inventario y metadatos bajo su licencia documentada; comprobar la licencia del snapshot exacto antes de importar y guardar evidencia.

No convertir recomendaciones de GitHub en garantías: antes de integrar, ejecutar un spike de compatibilidad y auditoría reproducible.

## 4. Arquitectura del repositorio

```text
exercise-motion-studio/
  AGENTS.md                          # instrucciones de ejecución, extraídas de este documento
  README.md                          # instalación/operación
  docs/
    SPEC.md                          # especificación maestra
    ARCHITECTURE.md
    LICENSE_POLICY.md
    BIOMECHANICS_QA.md
    KINETIC_MIGRATION.md
  apps/
    desktop/                         # WPF/WebView2 + front React/TS
    viewer/                          # visor Three.js sin backend obligado
  src/
    ExerciseMotion.Host/             # CLI, cola SQLite y orquestación .NET
    motion_pipeline/                 # Python: ingest/pose/solve/retarget
      ingest/
      pose/
      tracking/
      skeleton/
      constraints/
      qa/
      export/
    blender/
      build_scene.py
      retarget_avatar.py
      render_preview.py
      export_glb.py
    connectors/
      kinetic_adapter/
      supabase_export/               # disabled por defecto
      youtube_metadata/              # sólo referencias/metadatos permitidos
  assets/
    avatars/                         # diseños propios/CC0 verificados
    equipment/                       # modelos 3D + licencias individuales
    machine_profiles/                # partes, ejes, constraints, límites
    profiles/                        # calibraciones / humanoid skeleton
  tests/
    unit/
    integration/
    e2e/
    fixtures/                        # fuentes autorizadas y sintéticas
    golden/                          # trazas/capturas de referencia
  scripts/
    setup-windows.ps1
    doctor.ps1
    test-all.ps1
    batch-kinetic.ps1
  data/
    jobs/                            # excluido de Git
    catalogue/
    provenance/
  reports/
    IMPLEMENTATION_STATUS.md
    ITERATION_LOG.md
    TEST_RESULTS.md
    BLOCKERS.md
  .github/workflows/
  pyproject.toml
  uv.lock-or-requirements-lock.txt
  .gitignore
```

**Reglas de arquitectura:** interfaces pequeñas entre host, inferencia, retarget y render; errores tipados; objetos de dominio (`Exercise`, `MotionClip`, `RigProfile`, `EquipmentAsset`, `MachineProfile`, `MotionContact`, `AssetProvenance`, `Job`, `QaReport`); evitar una clase orquestadora monolítica. CLI plenamente utilizable antes de invertir en interfaz visual.

## 5. Modelo de datos y contratos

### 5.1 Identidad y procedencia de ejercicios

El adaptador Kinetic debe guardar `source_dataset = "kinetic"`, `source_exercise_id`, `source_revision`/hash, `internal_exercise_id` opcional, `exercise_name`, `movement_family`, `equipment_ids`, `source_youtube_url` como referencia, `rights_status`, `creation_method`, `qa_status` y `asset_version`.

**Regla:** nunca utilizar nombre visible como clave de unión; mapear por ID persistente y mantener tabla de correspondencias. Los datos de Kinetic se importan sin mezclar otras bibliotecas. No asumir que el catálogo permanece siempre en 908 elementos: guardar snapshot fechado, conteo y hash, y detectar altas/bajas/cambios.

### 5.2 Contrato canónico `motion.json`

```json
{
  "schemaVersion": "1.0.0",
  "coordinateSystem": "RH_Y_UP_METERS",
  "exerciseId": "kinetic:EXERCISE_ID",
  "source": {
    "type": "authorized_local_video",
    "sha256": "<SHA256>",
    "originUrl": null,
    "rightsEvidenceId": "RIGHTS-0001"
  },
  "fps": 30,
  "durationSeconds": 3.2,
  "rootMotion": [{"time": 0, "position": [0, 0, 0], "rotation": [0, 0, 0, 1]}],
  "bones": {
    "hips": [{"time": 0, "rotation": [0, 0, 0, 1]}],
    "leftUpperArm": [{"time": 0, "rotation": [0, 0, 0, 1]}]
  },
  "contacts": [
    {"start": 0.1, "end": 3.0, "actor": "leftHand", "target": "left_dumbbell.grip", "mode": "fixed_grip"}
  ],
  "equipment": [
    {"instanceId": "left_dumbbell", "assetId": "dumbbell_generic_v1", "profileId": "dumbbell_grip_v1"}
  ],
  "confidence": {"pose": 0.9, "tracking": 0.86},
  "method": "video_mocap",
  "review": {"status": "REVIEW_REQUIRED", "reviewer": null}
}
```

El ejemplo contiene valores ilustrativos, **no una captura real**. Concretar en `docs/SCHEMAS.md` o JSON Schema las definiciones completas: articulaciones obligatorias, referencia anatómica T/A pose, ejes y unidades, quaternions normalizados, origen de root, escala corporal, resolución temporal, lateralidad y convenciones de naming. Tests de ida/vuelta entre BVH/FBX/GLB si esos formatos se incorporan. No confundir `world landmarks` de MediaPipe (origen relativo a caderas) con una solución absoluta de escena ni con rotaciones de huesos.

### 5.3 Perfil de máquina

```json
{
  "profileId": "lat_pulldown_generic_v1",
  "assetId": "lat_pulldown_generic_glb_v1",
  "parts": ["frame", "seat", "handle", "cable", "weight_stack"],
  "joints": [
    {"part": "handle", "type": "prismatic", "axis": [0, 1, 0], "min": 0, "max": 0.9}
  ],
  "contactPoints": ["left_grip", "right_grip", "seat_support"],
  "constraints": ["two_hand_grip", "cable_length", "seat_contact"],
  "licenseEvidenceId": "ASSET-LIC-0001"
}
```

Cada máquina requiere geometría **propia o autorizada**, piezas móviles separadas, puntos de agarre, superficies de apoyo, límites mecánicos, relación entre partes y versión. Algunos equipos necesitarán perfiles cinemáticos a medida; no fingir que se deducen automáticamente de un clip.

## 6. Pipeline automático, paso por paso

### P-00 — Alta y validación de derechos

Crear `Job` con ID UUID, hash de entrada e idempotency key. Registrar tipo de origen, autor/titular declarado, derechos de procesamiento, prueba de licencia o autorización, uso permitido (análisis, transformación, comercialización de salida) y restricciones. Un enlace de YouTube de tercero **no** demuestra autorización. Sin evidencia suficiente, no ejecutar descarga ni inferencia sobre la fuente; estado `RIGHTS_REVIEW_REQUIRED`.

### P-01 — Ingestión y normalización

Validar contenedor/códec, tamaño, duración, fotogramas y único sujeto principal. Extraer copia normalizada a FPS configurable y resolución manejable; mantener timestamps, orientación y transformación de recorte. Registrar vídeo original inmutable mediante SHA-256 y excluirlo de paquetes comerciales. Rechazar archivos corruptos, vídeos sin persona visible o múltiples personas ambiguas (salvo selección explícita del sujeto).

### P-02 — Segmentación del ejercicio

Detectar comienzo y final de cada repetición o permitir rango manual; identificar fase concéntrica, excéntrica y pausas como anotaciones, sin asumir que el modelo infiere biomecánica clínica. Sugerir repetición representativa si hay varias. Conservar tanto trayectoria original como versión suavizada.

### P-03 — Pose corporal y manos

Ejecutar estimación de pose por frame y, donde haya agarres, seguimiento de manos. Asociar temporalmente landmarks mediante tracking de sujeto, detectar baja visibilidad y segmentos ocluidos. Persistir `pose_raw` con timestamps, confidencias por landmark, transformaciones 2D y landmarks 3D relativos. Calcular cobertura, estabilidad y lagunas; interpolación sólo dentro de umbrales documentados y marcando los fotogramas reconstruidos.

### P-04 — Reconstrucción del esqueleto y retarget

Construir un esqueleto canónico con longitudes consistentes, rotaciones locales, root motion, articulaciones limitadas y manejo de simetría izquierda/derecha. Adaptar del estimador de pose al rig mediante IK y corrección de ejes; estabilizar pies apoyados y evitar rotaciones imposibles. Al cambiar de avatar, conservar acción, apoyos y contactos y recalcular reach/IK. Retener datos fuente y transformados para comparar.

### P-05 — Detección y selección de equipamiento

Inferir categorías candidatas a partir de metadatos del ejercicio y seguimiento visual cuando exista un detector comercialmente autorizado. **La decisión final del asset se toma desde un catálogo versionado:** dumbbell, barbell, bench, kettlebell, mat, cable, machine, etc. Material no identificado -> `EQUIPMENT_UNRESOLVED`, nunca una mancuerna inventada para simular éxito.

### P-06 — Trayectorias, agarres, apoyos y máquinas

Para objetos libres: definir transform 6DoF de objetos y restricciones de agarre a mano(s); priorizar contacto rígido durante la fase de sujeción y gestionar soltado/apoyado. Para barra a dos manos: resolver el sólido mediante ambos puntos de agarre, sin escalado arbitrario. Para banco/máquina: resolver puntos de apoyo y límites; para poleas y palancas: animar jerarquías mecánicas según perfil cinemático. Física `Rigid Body` sólo cuando aporte (caídas/colisiones); **la técnica principal es animación esquelética + IK + constraints y cinemática**.

### P-07 — Construcción de escena

Blender en headless, escena en metros, orientación reproducible, avatar de referencia con rig comercialmente liberado, material/maquinaria propia, cámara(s), luces y suelo. Guardar `.blend` editable como opcional de producción. Exportar un GLB con avatar, animaciones y piezas móviles incorporadas. Validar que no se pierden skeleton bindings, nombres, textura, action, looping ni constraints bakeados al glTF.

### P-08 — Render de salidas

Generar una captura PNG representativa y secuencia corta WebP animada con fondo transparente o uniforme según preset; permitir vídeo MP4 propio opcional para canal de YouTube, con metadatos/voz fuera de alcance. Reducir tamaño y FPS sin romper el ciclo. Los vídeos originales nunca se incorporarán por accidente a `dist`.

### P-09 — Quality Assurance automática

Ejecutar métricas de integridad de archivos, continuidad temporal, valores NaN/Inf, longitudes óseas, límites articulares, contactos, foot skating, penetraciones y desacoples equipo-avatar. Renderizar al menos vistas frontal, lateral y tres cuartos, y comparar trayectorias con la referencia. Emitir JSON por regla con severidad, umbral, medición y frame. `QA_PASS` exige superar **todas** las reglas bloqueantes. Un vídeo de referencia técnicamente ambiguo debe producir `REVIEW_REQUIRED`, no `QA_PASS` por azar.

### P-10 — Revisión y aprobación

Panel con vídeo fuente permitido, avatar 3D, superposición de esqueleto y preview sincronizado, curvas articulares, equipo y alertas en timeline. Acciones: `approve`, `reject`, `repair`, `replace_source`, `change_avatar`, `select_equipment`, `adjust_constraints`, `reprocess`. Toda aprobación registra responsable, fecha, versión y hash. Para máquina compleja, la revisión humana es obligatoria mientras no exista validación suficiente de su perfil.

### P-11 — Packaging y exportación

Publicar sólo recursos aprobados y con licencias compatibles. Estructura estable:

```text
exports/kinetic/EXERCISE_ID/v0001/
  exercise.glb
  exercise.webp
  exercise.png
  motion.json
  equipment.json
  manifest.json
  licenses.json
  qa_report.json
  checksums.sha256
```

Exportación a Supabase únicamente tras aprobación explícita: ruta de Storage configurable, escritura idempotente, verificación de lectura y enlaces transaccionales a IDs existentes; staging/dry-run por defecto, sin eliminar assets existentes hasta completar validación y rollback.

## 7. Estados del trabajo, reintentos e idempotencia

Estados canónicos: `QUEUED`, `RIGHTS_REVIEW_REQUIRED`, `INPUT_VALIDATED`, `POSE_CAPTURED`, `MOTION_SOLVED`, `EQUIPMENT_RESOLVED`, `SCENE_BUILT`, `RENDERED`, `QA_FAILED`, `REVIEW_REQUIRED`, `APPROVED`, `EXPORTED`, `FAILED`, `BLOCKED`. Se guardan timestamp, versión de pipeline, exit code, stdout/stderr, consumo de RAM/VRAM, errores, hashes y reintentos.

- Reejecución de mismo vídeo + misma configuración + mismas versiones devuelve mismos identificadores/hashes esperables y reutiliza pasos válidos; `--force` crea versión nueva, no sobrescribe historia.
- Tareas seguras y reanudables. Si cae Blender durante render no recalcular pose ni borrar los resultados ya obtenidos.
- Política de reintentos automáticos para fallos transitorios (I/O, bloqueo temporal de archivo): límite de 3, backoff y registro. Fallos deterministas -> reparación de código/configuración, no bucle infinito.
- Gestión de cancelación y pausa con cleanup seguro, y reanudación desde último checkpoint coherente.
- En lote, limitar concurrencia por CPU/GPU y disco; establecer presupuestos por job en configuración, no tiempos de ejecución garantizados.

## 8. Requisitos de UX

**Pantalla de catálogo:** tabla con ID, nombre, equipamiento, vídeo fuente, evidencia de derechos, estado, calidad, miniatura, versión; filtros por falta de fuente, equipo, estado, bloqueos y errores.

**Pantalla de procesamiento:** arrastrar archivo; seleccionar ejercicio Kinetic; selector de avatar y equipo; pasos con logs y estimación de progreso por etapas (no porcentaje ficticio); cancelar/reintentar.

**Pantalla de revisión 3D:** controles Play/Pause, velocidad 0,25–2x, bucle, vista orbit, cámaras ortográficas, mostrar huesos, equipamiento, puntos de agarre, soporte, posiciones origen/destino; comparador temporal con vídeo; panel de alertas y navegación al frame afectado.

**Pantalla de lotes:** cola, prioridad, estados, errores, reintentos, selección masiva y exportación CSV/JSON de trazabilidad. No presentar un lote como completado si hay ítems pendientes de aprobación.

**Accesibilidad:** controles por teclado, estado textual además de color, mensajes de error accionables, UI responsive y sin exposición de rutas privadas en logs compartidos.

## 9. Pruebas obligatorias y criterios de aceptación

### 9.1 Matriz de casos reales (10 ejercicios piloto)

| ID | Ejercicio | Clase | Qué debe comprobarse |
|---|---|---|---|
| T01 | Sentadilla libre | Sin material | pies apoyados, cadera/rodilla, loop |
| T02 | Flexiones | Sin material, suelo | apoyo de manos y pies |
| T03 | Zancadas | Locomoción y alternancia | root motion, pie delantero/trasero |
| T04 | Curl con una mancuerna | Objeto unilateral | agarre y orientación del objeto |
| T05 | Curl con dos mancuernas | Dos objetos | independencia L/R |
| T06 | Press banca con barra | Banco y barra bilateral | espalda/banco, dos manos, trayectoria |
| T07 | Peso muerto con barra | Barra y suelo | cambio de apoyo, bisagra de cadera |
| T08 | Remo con mancuerna y banco | Sujeción y apoyo | contacto mano/banco y mancuerna |
| T09 | Jalón al pecho en polea | Cable/máquina | perfil de polea y desplazamiento de carga |
| T10 | Prensa de piernas | Máquina articulada | movimiento de plataforma, límites y respaldo |

Fuentes de prueba: clips propios o autorizados y muestras sintéticas con licencias archivadas. No publicar assets de referencia ajenos en Git. Si una prueba carece de vídeo autorizado, registrar bloqueo con identificación exacta del recurso pendiente y usar tests sintéticos adicionales, **sin dar la prueba real por aprobada**.

### 9.2 Reglas automáticas (umbrales iniciales, calibrables con fixtures)

- **VAL-01:** todos los JSON superan validación contra schemas versionados; rutas relativas seguras y hashes presentes.
- **VAL-02:** `exercise.glb` se importa de nuevo de forma headless y contiene armature, animación no vacía, duración > 0 y transformaciones finitas; al menos 2 instantes presentan poses distintas.
- **VAL-03:** variación de longitud de hueso de esqueleto canónico <= 1 % salvo correcciones de rig expresamente modeladas.
- **VAL-04:** sin NaN/Inf; sin saltos entre frames que excedan límites configurados por articulación y FPS; generar fallo con frames concretos.
- **VAL-05:** soporte de pie estable: desplazamiento no deseado <= 3 cm durante segmentos etiquetados de contacto, medido sobre la escena normalizada.
- **VAL-06:** agarre rígido: error de distancia entre mano y punto de agarre <= 3 cm durante segmentos confirmados, salvo ajuste aprobado por tolerancia de geometría; con barra bilateral se verifican ambos extremos.
- **VAL-07:** penetraciones cuerpo/equipamiento detectadas con collider simplificado; tolerancia y elementos exentos documentados; fallos severos bloquean.
- **VAL-08:** objeto no desaparece ni cambia arbitrariamente de escala durante los frames; máquina no sale de límites mecánicos.
- **VAL-09:** duración/ciclo exportado concordante con segmentos aprobados; WebP contiene más de un frame y movimiento visible; PNG no es completamente transparente.
- **VAL-10:** manifiesto de derechos completo, sin pesos/assets non-commercial o procedencia desconocida; bloquea exportación.
- **VAL-11:** render se inspecciona mediante vistas frontal/lateral/3-4; disponibilidad de artefactos de QA sin fallos de cámara o recorte.
- **VAL-12:** GLB se reproduce en navegador/Three.js en entorno de prueba y con el segundo avatar homologado; sin errores de consola ni pérdida de articulaciones.

**Nota técnica:** los umbrales de 3 cm son objetivos iniciales para escenas calibradas, no valores biomecánicos universales. Si por escala o geometría no son representativos, documentar y aprobar umbrales específicos por familia/equipo; nunca relajarlos silenciosamente para pasar tests. La similitud de pose de una sola cámara debe juzgarse además con vídeo de referencia y revisión de vistas 3D, ya que existe ambigüedad de profundidad.

### 9.3 Gates de entrega

**G0 — entorno limpio.** `setup`, `doctor`, tests unitarios y ejecución headless mínima sin Docker, con inventario de dependencias/licencias reproducible.

**G1 — movimiento básico.** T01–T03 aprobados, fichero `motion.json`, retarget a dos avatares, GLB + PNG + WebP, reporte QA y preview web.

**G2 — material libre.** T04–T08 aprobados, assets propios/CC0 y agarre sincronizado, sin teletransporte de objetos ni deslizamientos visibles.

**G3 — máquinas.** T09–T10 aprobados; plantillas cinemáticas versionadas, límites comprobados y revisión humana firmada.

**G4 — 10/10 piloto.** 10 casos reales con origen autorizado, QA automático PASS, revisión visual aprobada y exportación válida. **No basta con 10 archivos generados.**

**G5 — integración de catálogo.** Snapshot Kinetic completo importado con los IDs, sin duplicados ni modificaciones de Anvil Fitness; inventario por familia y fuente, backlog real de activos faltantes.

**G6 — catálogo completo.** 100 % de las entradas del snapshot de Kinetic tienen representación 3D aprobada, derechos documentados, GLB y previews verificadas y correspondencia exacta de ID. El objetivo inicial ronda 908; el número normativo es el del snapshot validado. Si algún ítem sigue `REVIEW_REQUIRED`/`BLOCKED`/`FAILED`, **G6 = FAIL**, aunque exista cobertura técnica parcial. Ninguna ejecución debe declarar G6 por estimación ni por tener placeholders.

**G7 — integración controlada.** Dry-run contra Supabase y después piloto de escritura con autorización, conteos antes/después, recuperación, rollback comprobado y ninguna regresión del catálogo existente. El producto independiente puede estar terminado en G6 sin ejecutar G7 si la integración se pospone explícitamente.

### 9.4 Evidencias mínimas exigidas

Cada gate aportará logs, comandos ejecutados, resultados de tests, capturas/renders, archivos exportados, hashes, versiones del software, licencias y un reporte `PASS | FAIL | BLOCKED` firmado con fecha. La revisión humana se incluye de forma explícita, no simulada por el agente.

## 10. Plan de implementación por iteraciones

### Iteración I0 — auditoría y bootstrap

Inspeccionar los repositorios candidatos y su estado real; comprobar compatibilidad, licencias, hashes/commits, versiones de Python/Blender/MediaPipe y los avatares; registrar dependencias descartadas. Crear estructura, schemas, CLI, instalación/doctor, fixtures y suite vacía de tests verificables. **Entregable:** G0.

### Iteración I1 — primera animación real

Ingestión y derechos, pose de vídeo autorizado, skeleton temporal, retarget a avatar propio, GLB, WebP/PNG y comparación temporal. Ajustar coordenadas y escala; corregir cualquier fallo en T01. **Entregable:** una sentadilla real validada, luego T02–T03; G1.

### Iteración I2 — objetos y bancos

Crear catálogo propio de geometrías parametrizadas (mancuerna, barra, discos, banco) con materiales simples. Anclajes, quaternions, transiciones de contacto y QA de agarre. **Entregable:** T04–T08; G2.

### Iteración I3 — maquinaria

Definir perfiles cinemáticos, piezas independientes, apoyos, poleas y límites mecánicos; fallback de revisión humana para equipo sin plantilla. **Entregable:** T09–T10; G3.

### Iteración I4 — automatización y UX

SQLite, jobs reanudables, CLI batch, WebView2/React o visor ligero equivalente, gestión de errores, QA visual, versiones y exportación. **Entregable:** G4 robusto.

### Iteración I5 — catálogo Kinetic

Importar snapshot, agrupar familias, mapear 44 tipos de equipos (referencia histórica a contrastar), detectar reutilización viable, fuentes autorizadas faltantes y gap de maquinaria; mantener board por ID. Procesar por lotes sin caer en degradación silenciosa. **Entregable:** G5 y avance medible hasta G6.

### Iteración I6 — salida a Anvil Fitness

Adaptador opcional de Supabase Storage/descriptores, validación readonly, dry-run, piloto aprobado, rollback, y cambio gradual de consumo de media por ejercicio. **Entregable:** G7 si hay autorización.

## 11. Protocolo obligatorio del agente: iterar hasta que funcione

> Este apartado constituye las instrucciones operativas para un agente de programación. Debe copiarse a `AGENTS.md` al inicializar el repositorio. Mantener el texto fiel y actualizado con el estado real.

### 11.1 Comportamiento

1. **Trabaja, no sólo planifiques.** Antes de escribir código, inspecciona el repositorio y el entorno; después implementa el siguiente requisito verificable de mayor prioridad. No pases varias ejecuciones elaborando diagnósticos repetidos sin intentar correcciones.
2. **Prueba todo cambio.** Tras cada incremento ejecuta tests relevantes y una prueba end-to-end del camino afectado. Antes de marcar un gate como PASS ejecuta `scripts/test-all.ps1` y los smoke tests correspondientes. Adjunta salidas reales, no supuestas.
3. **Itera con causalidad.** Si falla: identifica error reproducible -> hipótesis -> cambio mínimo -> reejecuta -> compara métricas -> conserva o revierte -> registra evidencia. Si hay tres intentos de solución sin progreso, modifica hipótesis/estrategia o reduce el problema a fixture mínimo; no repitas el mismo parche.
4. **No sustituyas funcionalidades por mocks** para conseguir un PASS engañoso. Los mocks sólo valen en unit tests; el gate E2E exige componentes reales y vídeos autorizados.
5. **No declares completado prematuramente.** Los estados admitidos son `NOT_STARTED`, `IN_PROGRESS`, `PASS`, `FAIL`, `BLOCKED`. No escribir `DONE` cuando existen pruebas sin ejecutar, revisiones humanas faltantes o fuentes sin permiso.
6. **Continúa por las tareas independientes** cuando un recurso externo esté bloqueado. La falta de un vídeo concreto no bloquea construir y probar el motor con otros vídeos autorizados.
7. **Prioriza integridad comercial.** Un activo no comercial, sin licencia o de origen dudoso bloquea exportación; no disimularlo con otro nombre ni borrar evidencias de origen.
8. **No mutar servicios externos** ni repositorios/app existentes sin consentimiento explícito. `dry-run` como ruta predeterminada para Supabase y YouTube.
9. **Genera una vista inspeccionable.** Si falla el render o la animación presenta artefactos, no basta con que el JSON y el GLB existan: reparar o marcar revisión.
10. **Registra las limitaciones físicas.** Oclusión, un único ángulo, imposibilidad de recuperar profundidad o una máquina desconocida deben reflejarse en confianza/review, no corregirse con afirmaciones inventadas.

### 11.2 Bucle de ejecución

```text
WHILE existe un criterio de aceptación pendiente y hay una tarea accionable:
    seleccionar la próxima tarea que desbloquea el gate más próximo
    identificar entradas, derechos, dependencias y estado de tests
    implementar el cambio más pequeño con resultado observable
    ejecutar tests unitarios, integración y E2E relevantes
    renderizar y comparar los frames de QA cuando hay animación
    comprobar las licencias de cualquier recurso añadido
    SI falla:
        registrar evidencia y causa probable
        reparar o revertir, y volver a ejecutar
    SI requiere aprobación o recurso externo:
        marcar sólo esa tarea BLOCKED, registrar solicitud exacta
        continuar con otra tarea independiente
    SI pasa:
        guardar archivos, hashes, logs, capturas y decisión de gate
        actualizar IMPLEMENTATION_STATUS.md y TEST_RESULTS.md
AL FINALIZAR CADA SESIÓN:
    entregar resumen comprobable: cambios, pruebas ejecutadas,
    gates PASS/FAIL/BLOCKED, artefactos y siguiente acción concreta
STOP sólo cuando G0..G6 = PASS (y G7 sólo si solicitado)
     o cuando no quede ninguna tarea accionable sin un bloqueo externo documentado.
```

**Restricción de honestidad:** el agente no debe prometer que continuará ejecutándose en segundo plano si su entorno no dispone de un scheduler o sesión persistente real. La instrucción de “no parar” se interpreta como iteración efectiva dentro de la ejecución disponible y reanudación mediante checkpoints en ejecuciones sucesivas; nunca como falsificación del estado final.

### 11.3 Archivos de seguimiento obligatorios

`reports/IMPLEMENTATION_STATUS.md`: matriz requisito/gate/estado/commit/fecha/evidencia.  
`reports/ITERATION_LOG.md`: cambios, hipótesis, fallos, intentos, decisiones y rollback.  
`reports/TEST_RESULTS.md`: comandos exactos, versiones, salidas y comparativas de métricas.  
`reports/BLOCKERS.md`: recurso faltante, dueño de la decisión, impacto, siguiente acción y alternativa independiente.  
`reports/LICENSE_AUDIT.csv`: recurso, URL, titular, licencia, evidencias, restricciones, estado comercial y fecha de validación.

### 11.4 Prohibiciones específicas

- No afirmar “100 % automático” para máquinas arbitrarias sin evidencia sobre el conjunto de pruebas.
- No convertir landmarks en rotaciones de huesos copiando valores numéricos sin transformación de coordenadas y control de jerarquía.
- No forzar exportación de GLB si no hay rig/huesos/animación realmente operativa.
- No confundir ausencia de excepciones con corrección biomecánica.
- No seleccionar assets de Mixamo/Renderpeople/Sketchfab/YouTube u otros por aparente gratuidad sin comprobar derechos de distribución en SaaS.
- No borrar ejercicios existentes, no modificar el proyecto Anvil Fitness en esta fase, no renombrarlo, no mezclar dataset externos.
- No reducir los umbrales de QA en secreto para declarar éxito.
- No sustituir vídeos de referencia legítimos por assets sintéticos para pasar gates que exigen casos reales.

## 12. Licencias, seguridad, privacidad y responsabilidades

### 12.1 Auditoría de licencias

Un repositorio MIT/Apache no convierte automáticamente en MIT/Apache los vídeos enlazados, pesos de modelos, clips Mixamo, rigs descargados o texturas. El auditor registra por cada archivo fuente y por cada recurso usado en el render: licencia exacta y versión, evidencia, derechos de transformación, uso comercial, atribución, distribución en GLB accesible por cliente y uso como material publicitario. CC BY puede exigir atribución; CC0 reduce obligaciones de copyright pero no elimina derechos de imagen, marcas o diseño. Los activos `NC`, `ND` incompatible, `editorial only` o con prohibición de distribución aplicable no se incluyen.

Si se usa una persona identificable en un vídeo fuente, considerar permisos de imagen y privacidad cuando proceda. La reconstrucción de un avatar genérico no justifica conservar y distribuir vídeo o rasgos personales ajenos. Guardar entradas originales localmente con acceso mínimo; permitir purgar al finalizar.

### 12.2 Seguridad de la aplicación

- No ejecutar scripts proporcionados por medios importados, no confiar en metadatos de archivos y limitar inputs de Blender/FFmpeg/Python.
- Normalizar rutas, impedir path traversal, controlar tamaño y formatos, usar carpetas temporales aisladas por job.
- Evitar ejecución de código remoto y modelos descargados sin hash y licencia verificados.
- No almacenar tokens de YouTube/Supabase en texto plano ni registrarlos en logs.
- Directorio `exports/` incluye sólo activos revisados y manifiestos sanitizados; `data/` y fuentes privadas excluidos de Git y del paquete comercial.

### 12.3 Política de YouTube

La URL puede enlazarse como referencia o utilizarse para reproducir el vídeo **a través del reproductor oficial** más adelante. El motor de MoCap no promete descargar o procesar cualquier URL: requiere archivo fuente autorizado o mecanismo de acceso legítimo. Una demostración alojada en YouTube no sustituye a la licencia de cada activo. Las visualizaciones del reproductor embebido dependen de la reproducción iniciada por el usuario y las reglas de YouTube; nunca prometer visitas o monetización garantizadas.

## 13. Rendimiento, escalabilidad y costes

La generación es un proceso **offline/por lotes**, no una inferencia por cada usuario de la app. La aplicación móvil/web sirve sólo GLB/WebP/PNG ya preparados. Los movimientos canónicos pueden compartirse entre variantes cuando el significado biomecánico se conserva. Cache por hash de vídeo, modelo, parámetros y avatar; procesamiento incremental en vez de rehacer 908 escenas en cada ajuste. Una vez normalizado `motion.json`, cambiar de avatar o material no debe obligar a repetir Pose Landmarker.

Presupuestar tamaño objetivo por asset y coste de Storage/CDN a partir de mediciones reales del piloto; no imponer límites arbitrarios que deterioren calidad. Evitar hardware cloud mientras el pipeline local cumpla requisitos. Incorporar métricas de tiempo por etapa, RAM/VRAM, FPS de render, tamaño y tasa de rechazo. Para el público final se ofrecerá WebP ligera con carga diferida y GLB sólo donde el modo interactivo aporte valor.

## 14. Definición inequívoca de terminado

Se puede declarar `MVP_COMPLETADO` sólo cuando **G0–G4 = PASS** con diez ejercicios reales autorizados, incluidos utensilios y dos máquinas, y evidencias de revisión visual/biomecánica. Se puede declarar `CATALOGO_KINETIC_COMPLETADO` sólo cuando **G0–G6 = PASS** y todas las entradas del snapshot tengan assets comerciales aprobados y validados. La incorporación a Anvil Fitness **no** forma parte del MVP y requiere autorización diferenciada para G7.

Si existe un bloqueo externo imposible de resolver desde el entorno, informar con estado `BLOCKED`, especificar qué permiso, archivo, modelo o revisión falta, aportar el trabajo sí completado y una forma de continuar; **no** presentar el proyecto como terminado. No se permite degradar requisitos para aparentar cumplimiento.

## 15. Prompt de inicio para el agente ejecutor

Copiar en la primera sesión de Codex, T3 Code, OpenCode o agente equivalente, acompañado de este archivo:

```text
Implementa íntegramente el proyecto descrito en ESPECIFICACION_MOCAP_3D_COMERCIAL.md.
Es un proyecto independiente para Windows y uso comercial, sin Docker.
Primero audita entorno, repositorios y licencias; después desarrolla el CLI y el
pipeline real, no una demo con mocks. Trabaja por los gates G0-G7 y por los casos
T01-T10. Tras cada cambio ejecuta pruebas reales, genera y revisa artefactos y
corrige las causas de fallo. Mantén los reportes de estado, resultados, bloqueos,
licencias, commits y hashes especificados en el documento. No declares PASS sin
pruebas reproducibles ni COMPLETADO con gates incompletos. Continúa con tareas
independientes si hay bloqueos; informa exactamente de permisos, vídeos o
revisiones humanas necesarios. No descargues vídeos ajenos de YouTube sin
habilitación, no incluyas activos no comerciales, no uses Docker y no modifiques
Anvil Fitness ni Supabase sin aprobación. No cambies estas condiciones para
conseguir que las pruebas pasen. Empieza ahora por I0/G0 y realiza trabajo
implementado y testeado, no solamente planificación.
```

## 16. Referencias técnicas y legales por validar en cada integración

- VideoIntoBlenderModel: https://github.com/s0ck3t/VideoIntoBlenderModel
- OpenGym3D: https://github.com/AssiamahS/opengym3d
- MediaPipe Pose Landmarker: https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker
- MediaPipe repository and license: https://github.com/google-ai-edge/mediapipe
- Blender Python glTF exporter: https://docs.blender.org/api/current/bpy.ops.export_scene.html
- Blender license and artwork: https://www.blender.org/about/license/
- Kinetic exercise dataset: https://github.com/kinetic-place/exercises-db
- YouTube embedded playback: https://support.google.com/youtube/answer/171780
- YouTube IFrame API: https://developers.google.com/youtube/iframe_api_reference

**Control de vigencia:** estas referencias se consultaron al redactar la especificación (17/11/2026). Antes de ejecutar cada integración, el agente debe fijar una versión/commit SHA y revisar de nuevo licencias, dependencias, compatibilidad, changelog y condiciones de uso. Este documento describe requisitos y estrategia; **no constituye evidencia de que el producto ya esté implementado ni de que el 100 % de Kinetic pueda generarse sin intervención humana**.