# G1 — real exercise video → Microsoft Rocketbox dual skinned GLB (TECHNICAL diagnostic)

**Gate G1: IN_PROGRESS / BIOMECHANICS_FAIL / HUMAN_VISUAL_NOT_APPROVED.**
This workflow is a genuine monocular MoCap/retarget prototype. No claimed IK,
equipment detection, proprietary distribution, exercise quality or completion.

## Reproducible source and licenses

- Exercise: Wikimedia Commons *Basic single leg squat.webm*, RickyBennison,
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
  Reference: https://commons.wikimedia.org/wiki/File:Basic_single_leg_squat.webm
  SHA256: `ab4602823ad00de3409eb50d2c65c6b1ce5566c5dca6753555ff2b19107db88e`.
  **Motion derivatives inherit obligations. Diagnostic files are not proprietary commercial assets.**
- Pose: MediaPipe Pose Landmarker Full task, SHA256
  `5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1`;
  pinned Python dependencies `requirements-pose.txt`. Model license record in `reports/LICENSE_AUDIT.csv`.
- Human assets: Microsoft Rocketbox original MIT, commit
  `0943055db6ec570bcef9f2c8b41c9e5467c808f9`,
  `Sports_Male_01`, `Sports_Female_02`, see `docs/ROCKETBOX_AVATARS.md`.
  Both full original MIT notices are copied beside the diagnostic GLBs.
- No YouTube-derived videos, RepDB, cloud processing, Anvil Fitness or Supabase changes.

## Pipeline

1. `scripts/fetch_rocketbox_sports.py`: fetch FBXs and textures authenticated by Git blobs, original MIT text.
2. `src/blender/import_rocketbox_sports.py`: original skinned humans, textures, .blend/GLB source asset.
3. `tests/integration/smoke_real_pose.py`: real FFmpeg/MediaPipe 47 frames (46 detected), `solved_skeleton.json`.
4. `src/blender/retarget_rocketbox_sports.py`: calibrate one real source→rig coordinate basis, map 16 observed-direction targets to **80-joint skin**, output 47-frame Blender animation, animated GLB, eight true full-body Blender frames/sex, SHA/license manifest and original attribution.
5. `scripts/encode-rocketbox-retarget-preview.py`: encode those eight renders as animated WebP.
6. `tests/asset/qa_rocketbox_real_retarget.py`: open both generated files; verify true deforming GLB, preserved 80-joint rig, non-root transforms, source-vs-output knee/elbow flexion, original timebases, world-scale toe-height estimate and full-body viewport coverage on eight real skinned poses.
7. `ems review-queue`: immutable, hash-linked queue for the real GLBs with human review, contact, attribution, angle and confidence failures. `release_gate=BLOCKED`.

## Important diagnosis: FBX bone tail is NOT a joint coordinate

The Rocketbox glTF root uses scale `0.01`, inherited from FBX/3ds Max
centimeters. On importing GLB, Blender can create **artificial edit bone tails**
many metres away from the anatomical child node. For example, a calf's
`posebone.tail` gave a fictitious location about 10–15 metres from the person.
The first G1 attempt had `maximum_vertical_root_correction_m≈14` and **blank
renders** even though static avatars and GLB skins passed.

The fix uses **`bone.head → child_bone.head`** for every anatomical segment,
including the ankle→toe support, in actual armature coordinates. Never aim at
`bone.tail` for this imported rig. Projection to world metres must include
`rig.matrix_world`; a raw vertex coordinate in the mesh is NOT automatically metres.
The first corrected CI produced max root shift `0.316/0.333 m`, actual
deformed mesh, 80 joints and real captured animation on both avatars.

The initial camera also clipped the shins: the corrected output fits a
camera over **evaluated skinned geometry at all eight observation frames**;
QA independently projects animated vertices back into the saved camera and
requires every sampled vertex inside the viewport.

## Verified execution and known failures

- Real capture from licensed human video: 47 frames, 46 detected, 1 held.
  86 low-visibility segment holds and 14 source-direction temporal clamps.
- Two genuinely animated GLBs, each with original Microsoft MIT notice,
  attribution and real render/WebP; 80 bones, 16 driven bones and stable skin.
- [Blender CI #44302626950 — SUCCESS](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44302626950):
  max vertical root 0.316/0.333 m, zero GLB/Blend support drift beyond 0.000013 m,
  141 source→avatar elbow/knee checks per variant,
  segment-length ratio error ~0.000001, GLB→Blend flexion delta ~0.001°.
- [Real full-body camera/animation CI #44303407819 — SUCCESS](https://github.com/akumanomi1988/Exercise-Motion-Studio/actions/runs/44303407819):
  eight actual poses/sex inside saved camera, PNG+WebP and genuine skins.
- **VISUAL REVIEW NOT APPROVED**: scene lacks calibrated global root motion,
  foot-plane IK, positive ground contact, pole-vector elbow/knee selection,
  hand grip and equipment. Characters can appear floating, and single-leg
  balance is not reliably reconstructed from this monocular video.
- **BIOMECHANICS SCREENING FAIL**:
  captured→retarget left knee >15° on 3 observed samples per avatar;
  peak `23.60°` around `2833 ms`. The observed single-leg knee angles also
  have rapid reversals, e.g. 86°→40°→113° over ~333 ms, and must be triaged
  rather than silently over-smoothed/approved. Model exports are coherent:
  the error is from temporal source filtering/retarget, not glTF serialization.
- No T01–T10 coverage claim and no exclusive/commercial asset acceptance.

## Offline local execution (Windows)

First register/source/solve as described in `docs/POSE_CAPTURE.md`, then:

```powershell
python scripts/fetch_rocketbox_sports.py --output-dir data/vendor/rocketbox_sports --variant both
foreach ($sex in @("male","female")) {
  blender -b --factory-startup --python-exit-code 10 --python src/blender/import_rocketbox_sports.py -- --source-dir "data/vendor/rocketbox_sports/$sex" --output-dir "data/generated_avatars/rocketbox_sports/$sex"
  blender -b --factory-startup --python-exit-code 10 --python src/blender/retarget_rocketbox_sports.py -- --solved data/qa-inference/solved_skeleton.json --attribution data/qa-inference/SOURCE_ATTRIBUTION.txt --avatar-dir "data/generated_avatars/rocketbox_sports/$sex" --output-dir "data/qa-inference/rocketbox_retarget_$sex" --fps 6
  python scripts/encode-rocketbox-retarget-preview.py --output-dir "data/qa-inference/rocketbox_retarget_$sex"
  blender -b --factory-startup --python-exit-code 10 --python tests/asset/qa_rocketbox_real_retarget.py -- --output-dir "data/qa-inference/rocketbox_retarget_$sex" --solved data/qa-inference/solved_skeleton.json
}
$env:PYTHONPATH = "src/motion_pipeline"
python -m ems review-queue --male-dir data/qa-inference/rocketbox_retarget_male --female-dir data/qa-inference/rocketbox_retarget_female --solved data/qa-inference/solved_skeleton.json --output data/qa-inference/rocketbox_review_queue.json
```

**Proven CI environment:** GitHub Actions Ubuntu + Blender 5.0.1; Windows
compatibility remains to be tested. Download model, video and source on a
system with network access; the inference/Blender processing itself is local.

Next: restore faithful >15° knee segments with interval-aware visibility,
pose confidence and physically plausible pole-vector IK; calibrate root/ground
with multi-view or floor observations; perform three-angle human visual review
with 10 truly authorized exercises before any commercial approval.
