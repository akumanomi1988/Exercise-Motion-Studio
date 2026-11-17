# Bootstrap CLI

**Status:** local registration, FFprobe metadata and complete FFmpeg decode now available. Pose extraction, 3D retarget, equipment tracking, renders and exports are NOT yet implemented.

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

Then verify actual media decoding before inference:

```powershell
python -m ems probe --job-id "<job_id_returned_by_register>"
# optional for long clips:
python -m ems probe --job-id "<job_id>" --decode-timeout-s 900
```

The `probe` step verifies that the file still matches its original SHA-256, reads video codec/resolution/FPS/duration via ffprobe, and decodes **every** frame with FFmpeg. It updates `media_probe` and `pipeline.probe = PASS` atomically. It does not infer a pose or upgrade `USER_ATTESTED` to `APPROVED`. `capture` stays `NOT_STARTED`. Invalid/mutated media returns an error and is not marked valid. A CI-generated test pattern is only a codec fixture, **never** a real exercise demonstration.

Never upload `data/` to GitHub. Refer to `AGENTS.md` for the implementation next steps.