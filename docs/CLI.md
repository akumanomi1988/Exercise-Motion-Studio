# Bootstrap CLI

**Status:** works only for local source registration and diagnostics. Pose extraction, 3D retarget, equipment tracking, renders and exports are NOT implemented by this bootstrap.

After cloning, from PowerShell:

```powershell
.\scripts\setup-windows.ps1
.\scripts\doctor.ps1
.\scripts\test-all.ps1
```

Or without installing a package, set `PYTHONPATH` to `src/motion_pipeline` and run `python -m ems doctor`.

Register a video with an auditable operator declaration:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src\motion_pipeline")
python -m ems register --source "C:\Videos\squat.mp4" --exercise-id "T01" --rights-basis owned --rights-evidence "Video grabado por el titular; contrato de cesion archivado X"
```

Returns `REGISTERED` and saves `data/jobs/<job-id>/manifest.json`. It does NOT decode or copy the source and does NOT certify the rights; operator evidence must be reviewed before commercial export. No YouTube downloader is included.

Never upload `data/` to GitHub. Refer to `AGENTS.md` for the implementation next steps.