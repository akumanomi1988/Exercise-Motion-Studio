# Microsoft Rocketbox Sports — avatares reales, riggeados, comerciales bajo MIT

Estado: **AG1 progreso técnico aprobado en Blender CI; G1 retarget y aprobación comercial de EMS NO aprobados**.

## Selección fijada

- Fuente oficial: https://github.com/microsoft/Microsoft-Rocketbox; `0943055db6ec570bcef9f2c8b41c9e5467c808f9` (Microsoft Research).
- Masculino: `Sports_Male_01`, `Assets/Avatars/Professions/Sports_Male_01/Export/Sports_Male_01.fbx` (SHA256 `dc63f02885e37786e0ed5c4d441f565dcfab4eac71f31a208edca74fe5cea8ed`).
- Femenino: `Sports_Female_02`, `Assets/Avatars/Professions/Sports_Female_02/Export/Sports_Female_02.fbx` (SHA256 `b96d9952e6e5d232ddd12e0ec844e371623d9922d03c73814299fd4dbc0a9710`). `Sports_Female_01` se descartó por vestimenta inadecuada para la biblioteca fitness.
- Materiales: colores y normales de cuerpo/cabeza, resolución original 2048×2048; cabello/transparencia de femenino también procedente de textura original verificada, no una pintura simulada.
- Licencia de origen: **MIT**, https://github.com/microsoft/Microsoft-Rocketbox/blob/master/LICENSE.md. SHA256 texto `17474e386e0b9e1a700cc3d06b2b0882a2c376d9c6b49c7f8274409b8f8d2352`. Conservar texto completo copyright (c) 2020 Microsoft junto a cada GLB / en su paquete. MIT sí permite uso, modificación y redistribución comercial. No confundirlo con certificación de calidad técnica o biomecánica de EMS.
- Esqueleto: un armature `Bip01`, **80 huesos por avatar**, dedos incluidos. Mapa semántico de 25 articulaciones compartido en `assets/rig_profiles/rocketbox_sports_humanoid_v1.json`. No forzar IDs o ejes del rig MPFB de 53 huesos previo.
- Avatares en formato `source.blend`, `avatar.glb`, `rest_review.png`, `asset.json`, `UPSTREAM_LICENSE.md`, `import_report.json`, `qa_report.json`.

## Descarga y conversión reproducibles (Windows / Linux, sin Docker)

```powershell
python scripts/fetch_rocketbox_sports.py --output-dir data/vendor/rocketbox_sports --variant both
foreach ($sex in @("male", "female")) {
  blender -b --factory-startup --python-exit-code 10 --python src/blender/import_rocketbox_sports.py -- --source-dir "data/vendor/rocketbox_sports/$sex" --output-dir "data/generated_avatars/rocketbox_sports/$sex"
  blender -b --factory-startup --python-exit-code 10 --python tests/asset/qa_rocketbox_sports.py -- --source-dir "data/vendor/rocketbox_sports/$sex" --output-dir "data/generated_avatars/rocketbox_sports/$sex"
  $env:PYTHONPATH = "src/motion_pipeline"
  python -m ems asset-check --asset-dir "data/generated_avatars/rocketbox_sports/$sex"
  # Expected denial: commercial release requires documented final review.
  python -m ems asset-check --asset-dir "data/generated_avatars/rocketbox_sports/$sex" --require-commercial
}
```

El importador usa `bpy.ops.wm.fbx_import` con Blender 5 y `bpy.ops.import_scene.fbx` en versiones anteriores. **Blender CI Ubuntu 26.04 / Blender 5.0.1** es el entorno realmente probado. Windows está por verificar.

## Evidencia real

- Blender E2E + QA: https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44297081493 **SUCCESS**, licencia MIT fuente y copia exacta junto a cada avatar.
- Python CI: https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44297081549 **SUCCESS**.
- Output masculino: 1,804148 m alto; 80 huesos; GLB con 4 imágenes PNG originales >=2048²; 4.235 vértices pesados tras reimportación; deformación evaluada de 0,250412 m al girar hueso superior derecho (prueba técnica, no gesto de ejercicio).
- Output femenino: 1,737497 m alto; 80 huesos; GLB con 5 imágenes originales >=2048², incluida transparencia; 5.433 vértices pesados tras reimportación; deformación 0,227177 m en misma prueba técnica.
- GLB reimportados, skinning real verificado, 25 bindings semánticos presentes en ambos esqueletos. Se inspeccionaron imágenes PNG de reposo y se corrigió la textura de transparencia del pelo femenino.
- Artifact temporal CI: https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44297081493 (el enlace concreto de artifact está disponible en ese run). Las fuentes originales y los exportados se generan localmente mediante script; no mantener decenas de MB de TGA en Git.

## Limitaciones no aprobadas

- La transferencia de un vídeo real a este rig aún **NO** se ha implementado ni probado; la PR #16 usa un rig MPFB diferente y sus renders **FALLAN** anatomía/biomecánica. No fusionarla hasta arreglar el solver, orientación, IK, apoyos y revisión visual.
- No hay agarre de material, contactos, colisión de cuerpos, restricciones articulares finales, manos operativas, prueba de sentadillas reales ni visual comercial aprobada.
- No convertir automáticamente una malla humana en rigid body; la animación se realiza con armature/skin y futura IK. Rigidbodies se reservan para física de objetos cuando corresponda.
- La licencia MIT del avatar es apta para explotación comercial si se cumple el aviso; **`asset.json.licenses.status=PENDING` y `distribution_approved=false`** hasta firma técnica/comercial. No publicar assets en Anvil Fitness/Supabase.
