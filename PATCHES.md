# Tellus fork of Distant Horizons — patch series

This repository (and its `coreSubProjects` submodule, `TimStewartJ/distant-horizons-core`) is a
fork of the official Distant Horizons mod, maintained as a **small patch series on top of official
release tags**. Both repositories keep the official history: `upstream-base` mirrors the official
`main`, and `main` is the official release base plus the patches below.

| | Official base | Fork branch |
| --- | --- | --- |
| Wrapper (this repo) | tag `3.2.0b` = `eb6bf9ae` | `main` |
| Core (`coreSubProjects`) | tag `3.2.0b` = `a0d2dfe4` | `main` |

Builds are versioned `3.2.0-b-tellus-fork.N` and tagged identically in both repositories.
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
| P1 | Tall-world Y packing and full-data format | Yucareux | 14-bit render Y (`RenderDataPointUtil.Y_WIDTH`), `FullDataSourceV2` / DTO / updater / propagator changes. **Not compatible with upstream LOD databases.** | Unlikely: persistent-format change for a niche use case. Permanent patch. |
| P2 | Tri-state world generator availability | Yucareux | `IDhApiWorldGenerator.getGenerationAvailability` (READY / SPLIT / UNAVAILABLE) so a data-backed generator can report cache state instead of blocking a worker. | Plausible; DH maintainers have said they would accept N-sized generation work (DH issue 1294). |
| P3 | Disable the self-updater for the Tellus distribution | Yucareux | Prevents an upstream jar from replacing this build. | Fork-only by nature. |
| P4 | Add Tellus LOD ingestion simulation task | Yucareux | `simulateTellusLodIngestion` profiling task. | Fork-only tooling. |
| P5 | Make the world-gen camera-speed pause configurable | TimStewartJ | `Config.Common.WorldGenerator.pauseGenerationAboveCameraSpeed` (0 disables); upstream hard-codes 20 blocks/s. | **Yes** — small, generic. |
| P6 | Keep coarse LODs rendering until all children hold real data | TimStewartJ | `keepLowerDetailLodsUntilChildrenHaveData`: a parent section stays visible while its children have only empty buffers, removing the hole that `upsampleLowerDetailLodsToFillHoles` papers over with database writes. | **Yes** — generic fix for N-sized generation. |
| P7 | Keep DH visible until native chunks are ready | TimStewartJ | Native-chunk readiness tracking (Sodium render sections), fade mask texture in the terrain shader, Iris shader-pack patching, `enableNativeChunkReadinessHandoff`. Falls back to normal clipping whenever a hook is unsupported. | Maybe, as a generic hook; the Sodium/Iris implementation is the fragile part. |
| P8 | Prioritize coarse terrain and harden renderer state | TimStewartJ | `GENERATION_PRIORITY` / `getPriorityRetrievalPos` so a coarse first paint runs before normal requests; renderer state hardening. | Plausible with P2. Note: adds API members without bumping the API minor version. |

### Wrapper (this repo)

| Commit subject | Author | Purpose |
| --- | --- | --- |
| Tellus distribution: version tellus-height.1 and ignore local artifacts | Yucareux | Version and `.gitignore` from the original flattened fork. |
| Point the core submodule at the Tellus core fork | TimStewartJ | `.gitmodules` → `TimStewartJ/distant-horizons-core`. |
| P5–P8 wrapper halves | TimStewartJ | Fabric mixins into Sodium (`RenderSectionManager`, `RenderSection`) and Iris (`IrisLodRenderProgram`, `IrisRenderingPipeline`, `TransformPatcher`), all `require = 0` and gated to MC 26.2 in `FabricMixinPlugin`; `GlNativeChunkReadinessTexture`; `SodiumAccessor`; version bumps. |
| Release 3.2.0-b-tellus-fork.2 from the proper fork layout | TimStewartJ | First build from these repositories; byte-identical to `fork.1` except the version strings. |

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

CI (`.github/workflows/ci.yml`) runs the core tests and builds both 26.2 jars on every push.
Releases (`.github/workflows/release.yml`) are cut by pushing a tag equal to `mod_version`
(`3.2.0-b-tellus-fork.N`) to **both** repositories at the commit pair to release; the workflow
verifies the pair, builds, and publishes the jars with SHA-256 sums as a GitHub Release.

## Moving to a new official release

1. `git fetch upstream` in both repositories; update `upstream-base`.
2. In core: `git rebase --onto <new core tag> 3.2.0b main` (resolve P1 first; it is the large one).
3. In wrapper: rebase the same way, then point `coreSubProjects` at the rebased core and bump the version.
4. Build, run `core:test`, compare the jar against the previous release, smoke-launch with Tellus and Tellus Expeditions.
5. Tag both repositories with the new `…-tellus-fork.N` version.

Drift check 2026-08-31 (`git apply --check --3way` of every patch onto official `main`, wrapper `06813e95` /
core `b7941876`, version `3.2.1-b-dev`, API 7.1.0): all nine core patches apply cleanly; in the wrapper only the
`mod_version` lines and the submodule pointer conflict, as expected.
