# Tellus fork of Distant Horizons — patch series

This repository (and its `coreSubProjects` submodule, `TimStewartJ/distant-horizons-core`) is a
fork of the official Distant Horizons mod, maintained as a **small patch series on top of official
Distant Horizons**. Both repositories keep the official history: `upstream-base` points at the official
commit the series is based on, and `main` is that base plus the patches.

| | Official base | Fork branch |
| --- | --- | --- |
| Wrapper (this repo) | tag `3.3.4` = `eb1007cb` (API 7.2.0) | `main` |
| Core (`coreSubProjects`) | tag `3.3.4` = `64410621` | `main` |

Builds are versioned `<official mod_version>-tellus-fork.N` (currently `3.3.4-tellus-fork.7`) and
tagged identically in both repositories. fork.1–fork.3 were built on tag `3.2.0b`, fork.4 on official
`main` two days before 3.3.0 (`3.2.1-b-dev`) and fork.5–fork.6 on tag `3.3.1`; their tags keep that history. Base the
fork on a release tag:
a version containing `dev` sets `ModInfo.IS_DEV_BUILD`, which turns on per-datapoint validation, leak
tracking and the nightly-build chat warning.
The upstream auto-updater is disabled in this build (see P3).

Why a fork exists at all: Tellus renders true-height Earth (Everest at 1:1 is ~8,849 m), which
does not fit Distant Horizons' 12-bit render Y coordinate. That change alters the on-disk LOD
format and cannot be delivered as a mixin or a config switch. Everything else in the series is
small and is expected to move upstream over time.

Tellus itself compiles against the **stock** DH API and reaches these additions by reflection,
so Tellus runs with stock Distant Horizons (degraded: holes while approaching, generation pauses
above 20 blocks/s, no readiness fade, no tall worlds). `TellusReflectionContractTest` in core pins
the names Tellus depends on.

## Patches (in commit order)

### Core (`coreSubProjects`)

| # | Commit subject | Author | Purpose | Upstreamable? |
| --- | --- | --- | --- | --- |
| P1 | Tall-world Y packing and full-data format | Yucareux | 14-bit render Y (`RenderDataPointUtil.Y_WIDTH`), `FullDataSourceV2` / DTO changes and batched parent propagation (`FullDataSourceV2.UpdateBatch`). **Not compatible with upstream LOD databases.** | Unlikely: persistent-format change for a niche use case. Permanent patch. |
| P2 | Tri-state world generator availability | Yucareux | `IDhApiWorldGenerator.getGenerationAvailability` (READY / SPLIT / UNAVAILABLE) so a data-backed generator can report cache state instead of blocking a worker. The hook receives the 3.2.0 request width (`WorldGenerationQueue.getAvailabilityRequestWidthInChunks`) because 3.2.1 widened `DataSourceRetrievalTask.widthInChunks` to the whole section. | Plausible; DH maintainers have said they would accept N-sized generation work (DH issue 1294). |
| P3 | Disable the self-updater for the Tellus distribution | Yucareux | Prevents an upstream jar from replacing this build. | Fork-only by nature. |
| P4 | Add Tellus LOD ingestion simulation task | Yucareux | `simulateTellusLodIngestion` profiling task. | Fork-only tooling. |
| P5 | Make the world-gen camera-speed pause configurable | TimStewartJ | `Config.Common.WorldGenerator.pauseGenerationAboveCameraSpeed` (0 disables); upstream hard-codes 20 blocks/s (3.2.1 adds the on/off switch `pauseIfMovingQuickly`). | **Yes** — small, generic. |
| P6 | Keep coarse LODs rendering until all children hold real data | TimStewartJ | `keepLowerDetailLodsUntilChildrenHaveData`: a parent section stays visible while its children have only empty buffers, removing the hole while children still hold no data. 3.2.1 made downward propagation unconditional and removed `upsampleLowerDetailLodsToFillHoles` with its `LodBuilding.Experimental` category; this patch restores both, with propagation off by default, because unconditional propagation writes every descendant section and feeds the chunk regeneration pass. | **Yes** — generic fix for N-sized generation. |
| P7 | Keep DH visible until native chunks are ready | TimStewartJ | Native-chunk readiness tracking (Sodium render sections), fade mask texture in the terrain shader, Iris shader-pack patching, `enableNativeChunkReadinessHandoff`. Falls back to normal clipping whenever a hook is unsupported. | Maybe, as a generic hook; the Sodium/Iris implementation is the fragile part. |
| P8 | Prioritize coarse terrain and harden renderer state | TimStewartJ | `GENERATION_PRIORITY` / `getPriorityRetrievalPos` so a coarse first paint runs before normal requests; renderer state hardening (3.2.1 caches the client level wrapper, so only the cancellation handling remains). | Plausible with P2. Note: adds API members without bumping the API minor version. |
| P9 | Keep coarse-first generation work-conserving | TimStewartJ | Bounds coarse priority to 75% while normal work exists, backs off retryable unavailable inputs without occupying workers, enforces the configured worker limit, and avoids regenerating complete priority ancestors. Coverage uses 3.2.1's plan-dependent required generation step. | **Yes** — generic scheduler fairness and retry behavior. |

### Wrapper (this repo)

| Commit subject | Author | Purpose |
| --- | --- | --- |
| Tellus distribution: version tellus-height.1 and ignore local artifacts | Yucareux | Version and `.gitignore` from the original flattened fork. |
| Point the core submodule at the Tellus core fork | TimStewartJ | `.gitmodules` → `TimStewartJ/distant-horizons-core`. |
| P5–P8 wrapper halves | TimStewartJ | Fabric mixins into Sodium (`RenderSectionManager`, `RenderSection`) and Iris (`IrisLodRenderProgram`, `IrisRenderingPipeline`, `TransformPatcher`), all `require = 0` and gated to MC 26.2 and 26.3 and to the loaded mod in `FabricMixinPlugin` (3.2.1 removed that plugin's loaded-mod check); `GlNativeChunkReadinessTexture`; `SodiumAccessor`; version bumps. |
| Release 3.2.0-b-tellus-fork.2 from the proper fork layout | TimStewartJ | First build from these repositories; byte-identical to `fork.1` except the version strings. |
| CI / Release workflows, PATCHES.md, fork.3 and fork.4 releases | TimStewartJ | Tag-driven builds and this document; version bumps. |
| Refuse Iris older than 1.11.4 on Minecraft 26.2 | TimStewartJ | Official 26.2 properties allow Iris 1.11.2, which lacks `IrisApi.isReverseZDuringShaders` and crashes on the first frame with a shader pack. |

### Fixes carried until upstream has them (since fork.7)

Generic fixes from the Slipway world-retention (leak) investigation and its shader-artifact investigation. A–G are
the commits prepared on official `main` for upstream merge requests (see "Upstream submissions"), cherry-picked with
`-x`; each one leaves the fork at the first rebase onto an official release that contains it.

| # | Commit subject | Repo | What it fixes | Upstream |
| --- | --- | --- | --- | --- |
| B | Unbind a level's world generators when it closes | core | `WorldGeneratorInjector` kept every loaded level's generator and so every closed world; concurrent binds could throw in `bind()`. | core !113 (open) |
| C | Clear the last frame's level references when the world closes | core | Static `ClientApi.RENDER_STATE`/`RENDER_PARAMS` kept the last rendered levels. | Prepared |
| E | Shut down the world gen progress updater thread when a level closes | core | One idle thread per closed level. | Prepared |
| A | Free the world gen slot of tasks that fail | core | Chunk conversion that throws never completed its task, so its generation slot stayed taken. Upstream's change also frees the slot of failed tasks; P9 already does that here, so only the conversion half applies. | core !111 (merged 2026-10-04); drop on the next rebase past `825597fd` |
| I2 | Re-decide the LOD render pass after DhApiBeforeRenderEvent | core | Iris sets its defer-transparent flag in that event, but the pass was chosen before it, so the first frame after every Iris pipeline creation ran a combined pass ("Unexpected; somehow the Opaque + Translucent pass ran with shaders on"). Official 3.3.4 still logs this once per pipeline. | Not submitted |
| D | Don't keep the last world gen params in a static field | wrapper | `ThreadWorldGenParams.previousGlobalWorldGenParams` kept the last level. | Prepared |
| F | Don't keep the last client level in the static render event params | wrapper | Static render event params kept the last `ClientLevelWrapper`. | Prepared |
| G | Only handle client-side block events in FabricClientProxy | wrapper | With a server in the same process, block callbacks cast a `ServerLevel` to `ClientLevel` and threw. | Prepared |

Measured with the DH-only leak harness (knowledge-base page `distant-horizons/upstreaming-roadmap`): after five worlds
opened and closed, official `main` (3.3.5-dev) kept all five in memory and gained DH threads with each world; with the
fixes none stayed and the thread count was flat.

## Upstream submissions

Generic fixes are prepared on fresh upstream `main` in a separate clone (`E:\dh-upstream`) and tracked in the
knowledge-base page `distant-horizons/upstreaming-roadmap`.

| Date | Upstream | What | Origin in this fork | Status |
| --- | --- | --- | --- | --- |
| 2026-09-30 | core [!111](https://gitlab.com/distant-horizons-team/distant-horizons-core/-/merge_requests/111) | Free the world gen slot of tasks that fail (a failed or throwing task kept its slot, so a level stopped generating after `threads + 1` failures) | Found in P2's `WorldGenerationQueue` changes | Merged 2026-10-04 (`825597fd`, unchanged) |
| 2026-10-04 | wrapper issue [#1332](https://gitlab.com/distant-horizons-team/distant-horizons/-/work_items/1332) | Closed singleplayer worlds stay in memory (all leak causes, harness evidence) | Leak fixes B–G | Open |
| 2026-10-04 | core [!113](https://gitlab.com/distant-horizons-team/distant-horizons-core/-/merge_requests/113) | B: Unbind a level's world generators when it closes (+ ConcurrentHashMap, 2 unit tests) | Leak fix B | Open |
| — | — | L1 `StepTerrain` biome manager | `slipway-leak-fix` | Dropped: fixed upstream in `41be6fcac` |

## Provenance

The series was extracted from `Yucareux/Tellus` branch `DH-Fork-Tellus`, whose "DH fork v1" commit
(`c4657269`) flattened the core submodule into the wrapper tree on top of official wrapper commit
`eb6bf9ae`. Yucareux's changes are re-applied here as focused commits with him as author. The
flattened branch is preserved in `TimStewartJ/Tellus` under the tags `archive/2026-08-31/DH-Fork-Tellus`,
`dh/3.2.0-b-tellus-height.3.readiness.6` and `dh/3.2.0-b-tellus-fork.1`. Upstream Tellus ships its own
`3.2.0-b-tellus-height.N` DH binaries from unpublished source; those are a different lineage from this fork.

## Building

```powershell
$env:JAVA_HOME = '<JDK 25>'
.\gradlew.bat fabric:assemble '-PmcVer=26.2.0'      # fabric\build\libs\DistantHorizons-fabric-<version>-26.2.jar
.\gradlew.bat neoforge:assemble '-PmcVer=26.2.0'    # neoforge\build\libs\DistantHorizons-neoforge-<version>-26.2.jar
.\gradlew.bat core:test      '-PmcVer=26.2.0'      # core unit tests, including TellusReflectionContractTest
```

Minecraft 26.3 jars build the same way with `'-PmcVer=26.3.0'`. The native-chunk readiness mixins (P7) are active on
Fabric 26.2 and 26.3. On any other version they compile to empty stubs, which must keep their `@Mixin` annotation:
the mixin config lists them for every version, and Mixin refuses to start when a listed class has none.

CI (`.github/workflows/ci.yml`) runs the core tests and builds the 26.2 and 26.3 jars on every push.
Releases (`.github/workflows/release.yml`) are cut by pushing a tag equal to `mod_version`
(`…-tellus-fork.N`) to **both** repositories at the commit pair to release; the workflow
verifies the pair, builds, and publishes the jars with SHA-256 sums as a GitHub Release. An optional
`.github/release-notes/<mod_version>.md` is inserted into the release notes.

## Moving to a new official release

1. `git fetch upstream` in both repositories; update `upstream-base`.
2. In core: `git rebase --onto <new core base> <old core base> main` (resolve P1 first; it is the large one).
   `rerere` helps across retries. `-X ignore-space-change` removes whitespace-only conflicts, but check the
   indentation of auto-merged hunks afterwards (it can leave re-nested blocks mis-indented).
3. In wrapper: rebase the same way, then point every commit that changes `coreSubProjects` at the matching
   rebased core commit and bump the version.
4. Build, run `core:test`, compare the jar against the previous release, smoke-launch with Tellus and Tellus Expeditions.
   Also compare `ModInfo.CONFIG_FILE_VERSION` and the requirements in the built `fabric.mod.json` with the previous
   release: a change there breaks existing installations and never shows up as a conflict (see fork.7 below).
5. Write `.github/release-notes/<mod_version>.md` if users have to know or do something. Push a `rebase/<base>` branch
   so CI builds it, then `main`, then tag both repositories (core first) with the new `…-tellus-fork.N` version.

Rebase 2026-09-17 (`fork.4`, from tag `3.2.0b` to official `main` wrapper `1ef1d458` / core `d354abe8`). Upstream
changes that matter to Tellus:

- Generator plans (`Config.Common.WorldGenerator.generatorPlan`, default `SURFACE_THEN_CHUNKS`) replace
  `enableDistantGeneration`/`distantGeneratorMode`. The generation step a stored column must reach depends on the
  plan: `SURFACE` above block detail and `FEATURES` at block detail. API columns written without a step
  (`IDhApiFullDataSource.setApiDataPointColumn(int, int, List)`) are recorded as `SURFACE`.
- Downward propagation now always runs from sections below detail 12 and flags leaves for the chunk regeneration
  pass (`surfaceRegenMaxDistancePercent`, default unlimited). P6 makes it optional again.
- `Server.Experimental.enableNSizedGeneration` (multiplayer coarse retrieval now follows the session's generator
  plan) and `upsampleLowerDetailLodsToFillHoles` no longer exist; Tellus skips missing entries.
- `RenderDataPointUtil` height/depth names became max/min Y; `shiftHeightAndDepth` was removed.
- Minecraft 26.2 clients with Iris need Iris 1.11.4 or newer (and therefore Sodium 0.9.2): official main calls
  `IrisApi.isReverseZDuringShaders`, and older Iris crashes on the first frame with a shader pack.

Yosemite check before release (copy of the Tellus fork.11 save, 10 minutes idle at the saved position, Tellus LOD
timing logs): with propagation always on and the default plan, Tellus ran 15,265 LOD tasks, 6,515 of them repeats,
and the database grew from 201 MB to 726 MB (7.7k to 268k rows). With propagation off it ran 362 tasks with no
repeats and no growth, but still rebuilt 81 complete block-detail sections because their columns are `SURFACE`.
With propagation off and `generatorPlan = SURFACE_ONLY` it ran only the 281 genuinely missing tasks. Tellus 0.8.4-fork.12
applies `SURFACE_ONLY` at runtime while its direct LOD generator is registered.

Rebase 2026-09-18 (`fork.5`, from official `main` `1ef1d458` / `d354abe8` to tag `3.3.1`): official 3.3.0 is that
base plus a version-string change, and 3.3.1 only rolls the shadow Gradle plugin back to 9.0.0, so the series
applied without changes. fork.5 is the first release that also publishes Minecraft 26.3 jars.

fork.6 (2026-09-19): the fork.5 Fabric 26.3 jar crashed at startup (`MixinSodiumRenderSectionNativeChunkReadiness
is missing an @Mixin annotation`), because the readiness mixins were empty, unannotated classes outside 26.2.
The stubs are now annotated, and the mixins are enabled on 26.3: their targets in Sodium 0.9.2+mc26.3 and
Iris 1.11.6+mc26.3 match the 26.2 builds (`TransformPatcher.patchDHTerrain` gained a parameter the hook does not
read). Checked in a 26.3 game with Tellus: handoff active through the default shader and through an Iris shader
pack, Tellus LOD generation in single-player and on a dedicated server, clean close. The 26.2 jars are unchanged
apart from the version.

Rebase 2026-09-30 (`fork.7`, from tag `3.3.1` to tag `3.3.4`). Upstream changes that matter:

- **Config file version 5** (`88caff58d`): DH deletes a config file with a lower `_version` and starts from defaults.
  Moving an installation from fork.6 means setting `_version = 5` before the first start (the bump exists to add
  `grass` to `blocksDontUseSideTextureCsv`, so add it there as well); every other setting then carries over.
- **Fabric Loader 0.19.5** is required by the Fabric jars, on 26.2 as well: `fabric.mod.json` now asks for the loader
  version the jar was built with (`c1959b8d7`), and 26.2 builds with 0.19.5 since `d0491973c`. fork.6 accepted any
  loader.
- Shader fixes for Minecraft 26.2+:
  - `95bbccaff`: DH toggled `GL_BLEND` for every draw buffer but updated Minecraft's per-buffer cache for buffer 0 only.
    Opaque terrain drawn after the LODs blended into Iris's G-buffers, showing as dark blotches on world blocks.
  - `eb5076971`: binds the lightmap for Iris.
  - `01b9370b5`: leaves GL state to Iris while a shader pack is active.
  - `12bda2234`: on 26.3 with Iris, DH renders inside Sodium's render group.
- The update propagator ignores database shutdown errors (`a5e7cde96`). Regeneration is off for pre-existing surface
  data (`293f33d84`), and LODs that would leave holes don't zoom (`13ee08048`).

The core series applied with one conflict: P1 in `FullDataUpdatePropagatorV2`, where `a5e7cde96`'s new catch body now
sits inside P1's batch loop. The wrapper conflicted only in the version lines and the four submodule pointers.
`git range-diff` against the fork.6 series shows no other change to any fork commit. Added: A–G and I2 (above).
Not carried over: the local branches `slipway-leak-fix` (L1–L8; fixed upstream or replaced by A–G) and
`slipway-iris-fixes` I1 (the same change as `95bbccaff`).

Checked before release, in game on Minecraft 26.3 Fabric (Sodium 0.9.2, Iris 1.11.6, Tellus 0.8.4-fork.15, Tellus
Expeditions 0.13.0):

- A copy of a save with a fork.6 LOD database, a spectator flight of eight 256-block steps, with the default shader
  and with Bliss 2.1.2: the Tellus LOD generator registers, its runtime overrides (P5, P6, generator plan) apply, the
  readiness handoff is active (through DH's OpenGL renderer and through the Iris DH shader), the database is
  extended, and no error is logged. The same flight on fork.6 with Bliss logs Iris's pass error once.
- Sections stored during that flight: 491 with the default shader on fork.6 and on fork.7. With Bliss, fork.6 stored
  490 and fork.7 stored 463 and 456 in two runs, but both fork.7 runs shared the machine with an unrelated CPU-heavy
  job and the fork.6 run did not. The pair was not repeated under equal load, so a slowdown with shaders is neither
  shown nor ruled out.
- A fork.6 config with `_version` set to 5 keeps its settings; no reset is logged.
- Slipway's client GameTests with Bliss: Minecraft's per-buffer blend cache matches GL at every sampled point of the
  frame, world blocks are lit evenly (the blotches of the 3.3.1-based builds are gone), and after ten world
  open/close cycles no closed server world stays in memory.

The Fabric 26.2 jar was started to the title screen (Fabric Loader 0.19.5, Tellus 0.8.4-fork.13). The NeoForge jars
were built but not started. Closing the game window while still in a world can log one "Quad Tree tick exception"
(a task rejected by a pool that is already shut down); official 3.3.4 has the same code.
