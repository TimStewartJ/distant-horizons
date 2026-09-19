# Tellus fork of Distant Horizons — patch series

This repository (and its `coreSubProjects` submodule, `TimStewartJ/distant-horizons-core`) is a
fork of the official Distant Horizons mod, maintained as a **small patch series on top of official
Distant Horizons**. Both repositories keep the official history: `upstream-base` points at the official
commit the series is based on, and `main` is that base plus the patches.

| | Official base | Fork branch |
| --- | --- | --- |
| Wrapper (this repo) | tag `3.3.1` = `f0cefb7a` (API 7.1.0) | `main` |
| Core (`coreSubProjects`) | tag `3.3.1` = `b0a5f350` | `main` |

Builds are versioned `<official mod_version>-tellus-fork.N` (currently `3.3.1-tellus-fork.6`) and
tagged identically in both repositories. fork.1–fork.3 were built on tag `3.2.0b` and fork.4 on official
`main` two days before 3.3.0 (`3.2.1-b-dev`); their tags keep that history. Base the fork on a release tag:
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
verifies the pair, builds, and publishes the jars with SHA-256 sums as a GitHub Release.

## Moving to a new official release

1. `git fetch upstream` in both repositories; update `upstream-base`.
2. In core: `git rebase --onto <new core base> <old core base> main` (resolve P1 first; it is the large one).
   `rerere` helps across retries. `-X ignore-space-change` removes whitespace-only conflicts, but check the
   indentation of auto-merged hunks afterwards (it can leave re-nested blocks mis-indented).
3. In wrapper: rebase the same way, then point every commit that changes `coreSubProjects` at the matching
   rebased core commit and bump the version.
4. Build, run `core:test`, compare the jar against the previous release, smoke-launch with Tellus and Tellus Expeditions.
5. Tag both repositories with the new `…-tellus-fork.N` version.

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
