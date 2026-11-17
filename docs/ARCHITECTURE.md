# Arquitectura objetivo y decisiones

**Estado:** diseño. No atribuir a este repositorio capacidades aún no implementadas.

## Flujo de datos
```text
Video autorizado -> registro/licencia -> normalización FFmpeg
-> landmarks 2D/3D relativos -> solución temporal y confianza
-> MotionClip canónico -> retarget sobre RigProfile
-> escena Blender + EquipmentAsset/MachineProfile + contactos/IK
-> QA físico/visual -> GLB + PNG + WebP + manifest
-> staging local -> publicación controlada (futura)
```

## Módulos y contratos
- `src/ExerciseMotion.Host`: futuro host .NET 10 para cola SQLite/CLI y coordinación.
- `src/motion_pipeline`: Python 3.11+ para análisis de entrada, pose y solución temporal.
- `src/blender`: escenas, retarget, equipamiento, exportación, render sin interfaz.
- `src/connectors`: interfaces independientes para Kinetic, YouTube metadata y exportación Supabase desactivada.
- `apps/desktop`: futura UI Windows WPF+WebView2+React.
- `apps/viewer`: futura vista Three.js de GLB.
- `reports/`: evidencia auditable, sin falsos PASS.

## Decisiones
1. `motion.json` canónico separa captura, avatar y equipamiento; cambios de rig no repiten inferencia.
2. El runtime web nunca realiza MoCap: consume assets precomputados.
3. Para maquinaria, usar modelos paramétricos y perfiles mecánicos; no prometer reconstrucción universal a partir de una cámara.
4. La referencia YouTube sólo registra URL. Para inferencia se requiere un archivo/flujo obtenido y procesado con permiso.
5. Todo recurso distribuible pasa por revisión de licencia, QA temporal, QA de contacto y QA visual.
6. No mezclar el repo con Anvil Fitness ni publicar automáticamente en Supabase.

## Plan de entrega
I0/G0: contratos, registro derechos, CLI, doctor, fixtures sintéticos y pruebas.
I1/G1: captura real, movimiento y retarget 2 avatares.
I2/G2: objetos libres y bancos.
I3/G3: poleas/prensa con perfiles cinemáticos.
I4/G4: piloto 10/10 autorizado y QA.
I5/G5–G6: inventario íntegro Kinetic y animaciones validadas.
I6/G7: sólo con autorización, integración Supabase y rollback.

Referencia normativa: [especificación completa](../ESPECIFICACION_MOCAP_3D_COMERCIAL.md).