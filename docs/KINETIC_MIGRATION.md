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

## Snapshot oficial fijado y primera auditoría real — 18/11/2026

- **Solo Kinetic** \`kinetic-place/exercises-db\`, commit normativo
  \`75d59701c749243f522149d5edd63ec4c6870e5e\`.
- \`es/exercises.json\` Git blob \`ae8835aadbcbb05a06d0a75d29c7b604045c09b4\`;
  \`es/equipment.json\` Git blob \`5b117cae1a416f1b4badb6eba81ae45634cebef1\`.
- Licencia de estos datos: MIT, Copyright (c) 2026 Kinetic.place,
  conservar LICENSE; no extiende derechos sobre los vídeos o miniaturas
  de terceros citados dentro de los registros.
- **Inventario verificado con archivos reales:** 908 ejercicios, 44 equipos,
  1086 asociaciones, 16 familias, once equipos sin ejercicio referenciador.
  Todos los 908 y los 44 siguen \`NOT_APPROVED/UNMAPPED\`: son gaps,
  no geometría. [CI 44364445904](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44364445904).

### Auditoría local reproducible (Windows PowerShell, sin Docker)

Descargar los JSON oficiales desde el commit fijado una vez, o copiarlos
a estas rutas desde una distribución original verificada:

\`\`\`powershell
$revision = "75d59701c749243f522149d5edd63ec4c6870e5e"
New-Item -ItemType Directory -Force data/kinetic-snapshot/es | Out-Null
foreach ($source in @("exercises", "equipment")) {
    $url = "https://raw.githubusercontent.com/kinetic-place/exercises-db/$revision/es/$source.json"
    Invoke-WebRequest -Uri $url -OutFile "data/kinetic-snapshot/es/$source.json"
}
$env:PYTHONPATH = "src/motion_pipeline"
python -m ems kinetic-audit --exercises data/kinetic-snapshot/es/exercises.json --equipment data/kinetic-snapshot/es/equipment.json --output data/kinetic-output/inventory.json
\`\`\`

El comando valida el hash Git de los inputs completos, los 908/44 IDs,
las asociaciones UUID y genera un índice exclusivamente de **metadatos**.
Lista cada ejercicio con sus equipos y cada equipo con número real de
ejercicios asociados, familia y estado pendiente. La salida es inmutable
para un snapshot dado; IDs, slug y relaciones se mantienen en español.

No descargar, conservar, incrustar ni publicar vídeos/miniaturas YouTube
desde Kinetic; no importar RepDB. La detección de máquinas y agarres
precisa **subtipos por ejercicio**, ya que las categorías \`Máquina\`
(72 asociaciones) y \`Polea\` (84) no describen un mecanismo concreto.
El backlog de activos debe reconciliarse contra el \`AssetCatalog\` real
por UUID y perfil cinemático. No se asignan assets por nombre/familia de
forma automática sin prueba de equivalencia. La ausencia de mapping o QA
aprobado bloquea G6 incluso si existe un GLB diagnóstico.
