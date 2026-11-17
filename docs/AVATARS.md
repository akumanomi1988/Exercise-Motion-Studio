# AG1 — Avatares MakeHuman/MPFB (estado técnico)

El generador `src/blender/build_mpfb_avatars.py` produce avatares adultos masculino y femenino con la malla base original de MakeHuman, rig `game_engine` y skinning real, en `.blend` y `.glb`. **No** implica que tengan el aspecto comercial definitivo, materiales PBR acabados, ropa auténtica con malla, IK, animación real ni calidad biomecánica validada.

## Origen y derechos

- Fuente upstream: https://github.com/makehumancommunity/mpfb2, commit fijo `9de0707fdc88438d7c53a1a2ac7937d9221e2431` (MPFB 2.0.18).
- Licencia upstream: https://github.com/makehumancommunity/mpfb2/blob/9de0707fdc88438d7c53a1a2ac7937d9221e2431/LICENSE.md. El código del add-on usa GPL-3.0-or-later; las mallas base, targets, rigs y pesos incluidos, CC0-1.0. Se usa el programa GPL **sólo durante autoría**; no se incluye su código en archivos GLB ni en el runtime propietario.
- Se crea el archivo .blend y el GLB desde los datos propios del repositorio upstream, sin assets extra de usuarios ni paquetes de ropa de procedencia incierta. El `asset.json` documenta `status=PENDING`, `distribution_approved=false` y revisión humana pendiente, incluso si toda la CI es correcta. No empaquetar el programa GPL sin evaluación específica de sus condiciones.
- El fichero upstream `src/mpfb/data/targets/macrodetails/macro.json` fija **low (valor 0) = female**, **high (valor 1) = male**. Detectamos visualmente una inversión en el generador original de PR #13 y añadimos validación de los valores del macro para impedir que se publiquen avatares con la morfología invertida.

## Generación y pruebas

El workflow `.github/workflows/avatar-ci.yml` descarga el commit fijo, crea la extensión MPFB para Blender 5, construye ambas mallas/rigs, vuelve a importar GLB, reabre BLEND y verifica una deformación real al rotar un hueso con pesos. `qa_dual_avatar.py` exige misma jerarquía (53 huesos) y topología (19.158 vértices originales), pero diferente digest morfológico entre variantes. Archiva durante siete días modelos, previews, manifiestos y evidencias técnicas.

La primera ejecución exitosa sobre PR #13 fue [44117210502](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44117210502), antes de corregir la inversión de morfología. **No utilizar ese artefacto original como modelos correctamente etiquetados.** La corrección se procesa en PR #15 con un nuevo pipeline de CI.

### Pendientes estrictos

Los materiales de ropa son zonas de superficie pintadas, no prendas con geometría y simulación propias. El exportador advierte que reduce las influencias de skinning a las cuatro de mayor peso por vértice. Falta inspeccionar cómo afecta a hombros, caderas y rodillas en animaciones reales. Un GLB con armature NO es suficiente: pasar retarget de `solved_skeleton.json` a ambos avatares, reproducir GLB en Three.js, probar soporte/contactos, aprobar apariencia y licencia final. Por tanto, **AG1 y G1 permanecen IN_PROGRESS**.
