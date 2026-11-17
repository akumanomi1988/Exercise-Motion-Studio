# Exercise Motion Studio

Herramienta independiente para Windows, sin Docker, destinada a convertir **vídeos autorizados** de ejercicios en movimiento 3D retargeteable, con interacción con equipamiento y exportación para productos comerciales.

> **Estado:** fase de arranque. Aún no existe un motor de captura 3D validado ni ejercicios finales aprobados. No confundir el plan con una implementación completa.

## Documentación normativa

- [Especificación maestra](ESPECIFICACION_MOCAP_3D_COMERCIAL.md)
- [Instrucciones del agente](AGENTS.md)
- [Arquitectura y decisiones](docs/ARCHITECTURE.md)
- [Política de uso comercial](docs/LICENSE_POLICY.md)
- [Estado y gates](reports/IMPLEMENTATION_STATUS.md)
- [Bloqueos](reports/BLOCKERS.md)

## Objetivo operativo

1. Entrada: vídeo local con derechos documentados y metadatos del ejercicio. Una URL de YouTube **no** autoriza descargarlo.
2. Extracción: landmarks, captura esquelética y reconstrucción temporal con evaluación de confianza.
3. Retarget: movimiento canónico independiente del avatar, aplicado a rigs autorizados.
4. Escena: equipamiento 3D propio/permitido, agarres, contactos y restricciones mecánicas.
5. Salida: GLB animado, WebP, PNG, motion.json, manifest de procedencia y QA.
6. Piloto: diez ejercicios reales, incluidas máquinas; sólo entonces ampliación del catálogo Kinetic.

## Entorno objetivo

- Windows 10/11, Python 3.11, FFmpeg, Blender LTS, .NET 10.
- GPU opcional; ruta CPU para operaciones base.
- CLI y pruebas antes de la aplicación de escritorio.
- Sin escritura automática en Anvil Fitness, Supabase o YouTube.

## Desarrollo

El documento `AGENTS.md` obliga a iterar, probar y registrar evidencias con estados PASS/FAIL/BLOCKED. Para iniciar: revisar `ESPECIFICACION_MOCAP_3D_COMERCIAL.md` y avanzar I0/G0. No activar publicación de medios sin licencias y revisión.

El repositorio es público: **no subir vídeos privados, identidades, secretos, pesos externos, modelos de terceros ni sus archivos binarios sin una licencia compatible y autorización verificable**.

## Licencia del código propio

Pendiente de decisión del titular. La disponibilidad pública del código no concede por sí misma una licencia de reutilización; ver `docs/LICENSE_POLICY.md`. Las licencias Apache/MIT de herramientas integradas y las licencias de assets se gestionan de forma independiente.
