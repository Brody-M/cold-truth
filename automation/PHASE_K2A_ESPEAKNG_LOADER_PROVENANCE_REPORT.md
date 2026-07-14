# Cold Truth — K2a espeakng-loader 0.2.4 Provenance Report

Date: 2026-07-13  
Phase: K2a — license and binary-provenance inspection only  
Status: **UNRESOLVED — do not use the installed Kokoro runtime**

## Scope and method

This was a read-only provenance review of the already-installed `espeakng-loader==0.2.4` distribution in the isolated K2 virtual environment. The review used static package files and non-sensitive filesystem metadata, plus official PyPI, official project-repository, and official upstream eSpeak NG material.

No Python package was imported or executed. No library was loaded. No model or voicepack was loaded. No inference, synthesis, audio generation, provider call, authorization action, or production activity occurred.

## Installed distribution findings

- Installed distribution: `espeakng-loader==0.2.4`
- Package directory: `C:\ColdTruthLocalTools\kokoro-venv\Lib\site-packages\espeakng_loader`
- Distribution metadata directory: `C:\ColdTruthLocalTools\kokoro-venv\Lib\site-packages\espeakng_loader-0.2.4.dist-info`
- Wheel platform tag: `py3-none-win_amd64`
- Wheel generator: `hatchling 1.27.0`
- Installed package license metadata: **absent**
  - No `License-Expression` field
  - No `License` field
  - No license classifier
  - No packaged `LICENSE`, `COPYING`, `NOTICE`, or third-party notice file was found
- Embedded source archive: none found

The official [PyPI 0.2.4 release](https://pypi.org/project/espeakng-loader/0.2.4/) likewise publishes no package-license declaration. Its Windows x86-64 wheel is `espeakng_loader-0.2.4-py3-none-win_amd64.whl`, with official wheel SHA-256 `41f1e08ac9deda2efd1ea9de0b81dab9f5ae3c4b24284f76533d0a7b1dd7abd7`. PyPI shows a 2025-01-17 upload and no source distribution.

## Python wrapper license assessment

The official [`thewh1teagle/espeakng-loader` repository](https://github.com/thewh1teagle/espeakng-loader) currently contains an MIT license and currently declares version `0.2.4`. That is useful present-day repository evidence, but it is not enough under the K2a evidence rule to bind the installed PyPI 0.2.4 wheel to that license:

- No official `v0.2.4` release or tag was established.
- No official source archive accompanies the PyPI 0.2.4 wheel.
- No exact source commit for the published wheel was established.
- The wheel itself omits a license file and license metadata.

Result: the wrapper may have been intended to be MIT-licensed, but the exact installed 0.2.4 artifact's license provenance is **not verified**. The current branch must not be treated as proof of the historical wheel's terms.

## Bundled native library and data

### Native DLL

- Filename: `espeak-ng.dll`
- Installed path: `C:\ColdTruthLocalTools\kokoro-venv\Lib\site-packages\espeakng_loader\espeak-ng.dll`
- Size: 419,328 bytes
- Local SHA-256: `646d387acbc7ac2aa45e3625aa00a6835ae5d446ff8b0748298c3900b4dde258`
- Wheel `RECORD` entry: `espeakng_loader/espeak-ng.dll,sha256=ZG04esvHrCqkXjYlqgCmg1rl1Eb_iwdIKYw5ALTd4lg,419328`
- Embedded Windows product/company/version metadata: none available
- Exact binary source repository commit or release: **not established**
- Exact build recipe/toolchain binding for this wheel: **not established**
- Match to an official upstream binary checksum: **not established**

### Data files

The wheel also bundles an `espeak-ng-data` tree containing compiled dictionaries, phoneme data, language definitions, and voice definitions. No separate license or source-provenance notice for these bundled files is included in the installed distribution.

### Upstream licensing

The official [eSpeak NG repository](https://github.com/espeak-ng/espeak-ng) identifies the project, including its shared-library form, as GPL version 3 or later. Its [official releases](https://github.com/espeak-ng/espeak-ng/releases) identify upstream release commits, including eSpeak NG 1.52 at commit `4870adf`.

The names and layout of the bundled DLL and data strongly indicate eSpeak NG-derived components. If they are derived from upstream eSpeak NG, the upstream GPL-3.0-or-later terms are the relevant baseline. However, K2a could not prove that the installed DLL was built from release 1.52, commit `4870adf`, or any other exact upstream revision. It also could not locate corresponding-source or redistribution notices in the installed wheel.

Result: the likely upstream license family is identifiable, but the exact binary/data provenance and compliance chain for the installed artifacts are **not verified**.

## Runtime role of the loader

Static inspection of the package's `__init__.py` shows that it:

- Returns the bundled Windows `espeak-ng.dll` path.
- Returns the bundled `espeak-ng-data` path.
- Provides a `ctypes.CDLL` loading helper.
- Provides platform-specific shared-library availability helpers.

The package metadata documents passing those bundled paths to the phonemizer layer. Structurally, the wheel is intended to supply Kokoro's runtime phonemization dependency on Windows without requiring a separately installed native eSpeak NG package. Therefore, removing or ignoring the loader would leave the installed English-language Kokoro dependency path without its documented phonemization support. This is a static architecture finding only; runtime behavior was not tested.

## Required K2a determinations

| Question | Determination |
|---|---|
| License of the exact Python wrapper wheel | **Unresolved.** Current official repository shows MIT, but no version-specific official binding to the installed PyPI 0.2.4 wheel was established. |
| Bundled DLL filename and hash | `espeak-ng.dll`; SHA-256 `646d387acbc7ac2aa45e3625aa00a6835ae5d446ff8b0748298c3900b4dde258`. |
| Bundled DLL source | Apparently eSpeak NG-derived, but its exact source revision, official binary identity, and build provenance were not established. |
| Bundled DLL/data license | Upstream eSpeak NG is GPL-3.0-or-later; applicability is strongly indicated, but the wheel provides no artifact-specific notice or verifiable source binding. |
| Exact source commit or tag for loader 0.2.4 | **Not established.** |
| Exact upstream commit used for the DLL/data | **Not established.** Upstream 1.52 commit `4870adf` exists, but no evidence binds this installed DLL to it. |
| Is the loader needed at runtime? | **Yes, for the installed documented Windows phonemization path.** It supplies the native library and data paths used by the phonemizer integration. |
| Can K2 proceed under the provenance gate? | **No.** |

## Conclusion and recommendation

**Conclusion: UNRESOLVED.**

This is more than a missing cosmetic metadata field. The installed wheel contains a native DLL and a substantial upstream-derived data tree, but does not provide a license notice, corresponding-source pointer, exact upstream revision, reproducible build binding, or official binary checksum match. The Python wrapper's current MIT repository license also cannot be safely back-applied to the exact historical wheel without a version-specific official link.

Recommendation: **stop using this Kokoro dependency path and investigate another local TTS stack.** Keep the K2 environment frozen only as an inactive audit artifact; do not import it, run it, connect it to K1, or use it for synthesis. Any reconsideration would require a new, separately authorized provenance/compliance phase supported by authoritative version-specific evidence.

This report is an engineering provenance assessment, not legal advice.

## State confirmation

- Files created in K2a: this report only
- Package installation, uninstall, repair, or modification: not performed
- Python package import or execution: not performed
- Native DLL load or process launch: not performed
- Model or voicepack load: not performed
- Inference, synthesis, narration, audio, or media creation: not performed
- Credentials, environment variables, private configuration, account data, or secrets accessed: no
- MCP, ElevenLabs, provider, API, or network TTS request: no
- Authorization created, inspected, consumed, or changed: no
- Real-case or production material accessed: no
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`
- C4 approval created or consumed: no
- Rendering, upload, scheduling, publishing, or production activity: no
- Publishing and real-production modes remain disabled

STOP FOR HUMAN REVIEW.
