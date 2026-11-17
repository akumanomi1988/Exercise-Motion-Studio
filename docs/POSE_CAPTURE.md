# I1: captura de pose real (aún sin retarget)

**Estado:** el CLI implementa una etapa de inferencia real con MediaPipe Pose Landmarker Full para archivos locales ya registrados/probados. Produce \`pose_raw.json\` con 33 landmarks por pose, confianza, timestamps y coordenadas 3D relativas a cadera; **no** produce \`motion.json\` canónico resuelto, avatar riggeado, IK, contacto, GLB comercial ni aprobación de G1.

## Preparación local Windows (sin Docker)

Instalar Python 3.11 x64, FFmpeg/FFprobe, Blender LTS y (más adelante) .NET. Crear un entorno virtual como en \`scripts/setup-windows.ps1\`. Instalar la dependencia opcional fuera de la ruta de registro simple:

\`\`\`powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-pose.txt
.\scripts\install-pose-model.ps1
\`\`\`

Se usa una versión exacta del modelo publicado por Google:
\`https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task\`

SHA-256 fijado:
\`5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1\`

El bundle se almacena localmente en \`data/models\` (ignorado por Git). Nunca se descarga silenciosamente por el comando \`capture\`.

## Entrada y captura

\`\`\`powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src/motion_pipeline')
python -m ems register --source "C:\Videos\sentadilla.mp4" --exercise-id "T01" --rights-basis owned --rights-evidence "Referencia al permiso/titular verificable"
python -m ems probe --job-id "<job-id>"
python -m ems capture --job-id "<job-id>" --model "data\models\pose_landmarker_full.task" --model-sha256 "5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1"
\`\`\`

\`register\` no demuestra titularidad; incluso tras \`capture\` el estado comercial permanece bloqueado y la revisión de licencias es obligatoria. La captura requiere SHA inmutable del vídeo, prueba FFmpeg completa, modelo local y hash correcto. La salida en \`data/jobs/<job-id>/pose_raw.json\` incluye fotogramas con estado \`DETECTED\`, \`MISSING\` o \`AMBIGUOUS\`; los fotogramas de más de una persona no se asignan arbitrariamente.

### Semántica 3D

Los landmarks 3D de MediaPipe son **hip-relative**. No equivalen a traslación absoluta del sujeto, escala de escena calibrada ni rotaciones locales de un esqueleto riggeado. Se incluyen observaciones normalizadas en RGB letterbox 512×512 y una remuestreada CFR por FFmpeg a 8 FPS por defecto. Se conserva la indicación de que los timestamps originales de VFR aún no están reconstruidos: una fuente VFR exige trabajo adicional para sincronización precisa.

El código no inventa trayectorias cuando hay oclusión. Sus métricas \`detection_coverage\`, \`mean_core_visibility\` y \`ambiguous_frames\` son informativas y no sustituyen QA biomecánica o revisión humana.

## Prueba independiente con humano real

CI \`.github/workflows/pose-ci.yml\` utiliza un **vídeo auténtico** publicado como obra propia en Commons, no procedente de YouTube: [Basic single leg squat](https://commons.wikimedia.org/wiki/File:Basic_single_leg_squat.webm), por **RickyBennison**, con licencia [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

El SHA-256 del vídeo se fija a \`ab4602823ad00de3409eb50d2c65c6b1ce5566c5dca6753555ff2b19107db88e\`. No se hace commit del vídeo, el modelo, el archivo temporal de pose ni el contenido privado de otros usuarios. Un diagnóstico visual derivado del vídeo, cuando se produce, conserva la atribución/SA, y nunca se declara activo comercial aprobado. Este ensayo NO cumple los diez casos T01–T10: es una primera comprobación técnica del motor sobre una persona real.

## Licencias / próximos pasos

- Código MediaPipe Python: Apache 2.0 según upstream; versión opcional fijada \`mediapipe==0.10.35\`.
- Modelo Full v1: Google confirma Apache 2.0 para el bundle exacto en [issue 6306, respuesta oficial](https://github.com/google-ai-edge/mediapipe/issues/6306). Registrar hash exacto y revisar obligaciones de atribución/redistribución cuando se empaquete el instalador.
- Material Commons: CC BY-SA 4.0, con atribución y condiciones para derivados; **no incluirlo como medio comercial propio**.
- Siguiente iteración: estimación temporal con tracking/calibración, clip canónico, avatares comerciales masculino/femenino, retarget y QA visual real. Sin esas piezas **G1 sigue NO APROBADO**.

## Diagnóstico 3D no comercial desde captura auténtica

Si ya existe `pose_raw.json` generado realmente por MediaPipe, se puede inspeccionar la trayectoria con:

```powershell
blender -b --factory-startup --python-exit-code 10 --python src/blender/visualize_raw_pose.py -- --pose-raw data/qa-inference/pose_raw.json --output-dir data/qa-inference/diagnostic
blender -b --factory-startup --python-exit-code 10 --python tests/asset/qa_pose_debug.py -- --asset-dir data/qa-inference/diagnostic
python scripts/encode-pose-preview.py --asset-dir data/qa-inference/diagnostic
```

El diagnóstico crea `pose_debug.glb` con puntos/segmentos animados reales, `pose_debug.png` y `pose_debug.webp` de varios frames. **No es un avatar**, no tiene skinning, huesos anatómicos, IK, calibración, corrección de colisiones ni root motion absoluto. Su estado es `TECHNICAL_VISUALIZATION_ONLY` y queda bloqueado para distribución comercial. Verifica que el GLB contenga animación al reimportarlo, no que esa animación represente fielmente la biomecánica.

En [CI real 44109871802](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44109871802), el modelo detectó 46/47 frames de un humano verdadero; Blender exportó y reimportó 51 mallas/acciones animadas, PNG y WebP 8 frames. Las vistas inspeccionadas presentan movimiento visible, pero articulaciones inestables y segmentos no anatómicos: **no aprobar como recurso final**.

El vídeo de RickyBennison conserva CC BY-SA 4.0; cualquier redistribución de derivados debe revisar atribución y ShareAlike. El archivo CI incluye `SOURCE_ATTRIBUTION.txt`, y no publica el MP4/WebM original ni el modelo de Google. Los artefactos CI expiran a los siete días.
