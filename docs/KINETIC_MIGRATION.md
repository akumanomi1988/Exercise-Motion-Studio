# Reconstrucción del catálogo Kinetic

**Alcance exclusivo:** dataset Kinetic. No importar RepDB ni bases adicionales.
**Fase:** investigación/staging independiente; no conectar por defecto Anvil Fitness.

- Obtener snapshot fijado por commit y verificar licencia de CADA campo y media.
- Censar IDs de origen (referencia histórica ~908: no usar como número normativo sin contrastar snapshot).
- Importar metadatos/taxonomía/equipamiento sin alterar su identidad; mapear variantes biomecánicas con revisión.
- Mantener por ID el estado de cobertura, medio final, derechos, errores de QA y deuda de máquinas.
- Reutilizar movimientos maestros sólo cuando la variante sea funcionalmente equivalente.
- No publicar vídeos de YouTube como activos locales sin derechos comprobados.
- Generar GLB/WebP/PNG por ID, con manifest de origen, hash, referencias de avatar/equipo y estado aprobado.
- 100 % significa CADA ejercicio del snapshot aprobado y probado, sin placeholders ni revisión pendiente.
- Exportación a Supabase: dry-run + conteos + rollback y permiso explícito del propietario.

Las publicaciones de Kinetic no transfieren automáticamente permisos comerciales de vídeos externos enlazados.