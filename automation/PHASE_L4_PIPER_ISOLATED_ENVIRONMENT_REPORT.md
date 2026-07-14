# Cold Truth — L4 Piper Isolated Environment Report

Date: 2026-07-13  
Phase: L4 — cached-artifact install only  
Outcome: **READY FOR L5 RUNTIME HEALTH REVIEW**

## Scope completed

One sealed Python environment was created for exactly Piper 1.4.2 and exactly the `en_US-ljspeech-high` runtime assets. Piper and all mandatory dependencies were installed only from preselected, hash-verified binary wheels. Network dependency resolution was disabled during installation.

No Piper, ONNX Runtime, application-dependency module, application-package entry point, model, configuration, or audio path was imported, executed, or loaded. The environment's bundled `pip` installer was used only for the explicitly authorized local-wheel installation and metadata inventory.

## Python and isolated paths

| Item | Exact value |
|---|---|
| Environment-creation interpreter | `C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` |
| Python version | `3.12.13` |
| Isolated Piper environment | `C:\ColdTruthLocalTools\piper-1.4.2-venv` |
| Environment Python | `C:\ColdTruthLocalTools\piper-1.4.2-venv\Scripts\python.exe` |
| Verified dependency wheelhouse | `C:\ColdTruthLocalTools\piper-1.4.2-venv\wheelhouse` |
| Runtime assets | `C:\ColdTruthLocalTools\piper-1.4.2-assets` |
| Read-only Piper wheel source | `C:\ColdTruthLocalTools\piper-provenance-cache\wheel` |
| Read-only model/config source | `C:\ColdTruthLocalTools\piper-provenance-cache\model` |

The environment was created only at the authorized path. No global, user, project, Kokoro, Voicebox, Codebase Memory, or production Python environment was modified.

## Locked Piper wheel

| Field | Exact value |
|---|---|
| Package | `piper-tts` |
| Version | `1.4.2` |
| Wheel | `piper_tts-1.4.2-cp39-abi3-win_amd64.whl` |
| Official source | `https://files.pythonhosted.org/packages/c5/5a/fda959ca07554a8ec3e380b168e79fff16f3020f4956c356a613616c1994/piper_tts-1.4.2-cp39-abi3-win_amd64.whl` |
| Installed from | `C:\ColdTruthLocalTools\piper-provenance-cache\wheel\piper_tts-1.4.2-cp39-abi3-win_amd64.whl` |
| SHA-256 | `9c4a3a11f5889ea9d0df4414dce2bd9bee5ce7d9cf604c8fd5e307441d4c031f` |
| License | `GPL-3.0-or-later` |
| Provenance | Exact SHA-256 match to the PyPI Trusted Publishing attestation recorded in L3 |

The cached wheel hash was rechecked immediately before installation. The source cache was not altered.

## Mandatory dependency closure

Official Piper 1.4.2 metadata requires:

- `onnxruntime>=1,<2`
- `pathvalidate>=3,<4`

Official ONNX Runtime 1.27.0 metadata requires:

- `flatbuffers`
- `numpy>=1.21.6`
- `packaging`
- `protobuf>=4.25.8`

No optional extras were selected. The four latter packages declare no mandatory runtime dependencies in their selected release metadata, and PathValidate declares no external mandatory dependency. The complete application-package closure is therefore seven packages including Piper.

## Complete installed dependency lock

| Package | Exact version | Binary wheel and official PyPI source | SHA-256 | License metadata | Verification |
|---|---:|---|---|---|---|
| `piper-tts` | 1.4.2 | `piper_tts-1.4.2-cp39-abi3-win_amd64.whl` — `https://files.pythonhosted.org/packages/c5/5a/fda959ca07554a8ec3e380b168e79fff16f3020f4956c356a613616c1994/piper_tts-1.4.2-cp39-abi3-win_amd64.whl` | `9c4a3a11f5889ea9d0df4414dce2bd9bee5ce7d9cf604c8fd5e307441d4c031f` | GPL-3.0-or-later | Cached attested wheel; exact match |
| `onnxruntime` | 1.27.0 | `onnxruntime-1.27.0-cp312-cp312-win_amd64.whl` — `https://files.pythonhosted.org/packages/4f/88/8ec9db1a4d126bb8b758992beb40d1249df171917d75f44a327eb5f20dda/onnxruntime-1.27.0-cp312-cp312-win_amd64.whl` | `20c321cf187ba496e648acf6b4cf90b4d398b0d17c2a77fdaeba365b908cc1c1` | MIT License | Official binary; exact hash match |
| `pathvalidate` | 3.3.1 | `pathvalidate-3.3.1-py3-none-any.whl` — `https://files.pythonhosted.org/packages/9a/70/875f4a23bfc4731703a5835487d0d2fb999031bd415e7d17c0ae615c18b7/pathvalidate-3.3.1-py3-none-any.whl` | `5263baab691f8e1af96092fa5137ee17df5bdfbd6cff1fcac4d6ef4bc2e1735f` | MIT License | Official binary; exact hash match |
| `flatbuffers` | 25.12.19 | `flatbuffers-25.12.19-py2.py3-none-any.whl` — `https://files.pythonhosted.org/packages/e8/2d/d2a548598be01649e2d46231d151a6c56d10b964d94043a335ae56ea2d92/flatbuffers-25.12.19-py2.py3-none-any.whl` | `7634f50c427838bb021c2d66a3d1168e9d199b0607e6329399f04846d42e20b4` | Apache 2.0 | Official binary; exact hash match |
| `numpy` | 2.5.1 | `numpy-2.5.1-cp312-cp312-win_amd64.whl` — `https://files.pythonhosted.org/packages/65/66/53f31807a48a750f9d748da273bc3fcedd12b27ff1f3e373bfec55ef2dc0/numpy-2.5.1-cp312-cp312-win_amd64.whl` | `f7d60026c0bdb1380e83bfa7a0419c4577ee4b9a08880afcb6dadeb74c649fa2` | `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` | Official CPython 3.12 Windows binary; exact hash match |
| `packaging` | 26.2 | `packaging-26.2-py3-none-any.whl` — `https://files.pythonhosted.org/packages/df/b2/87e62e8c3e2f4b32e5fe99e0b86d576da1312593b39f47d8ceef365e95ed/packaging-26.2-py3-none-any.whl` | `5fc45236b9446107ff2415ce77c807cee2862cb6fac22b8a73826d0693b0980e` | `Apache-2.0 OR BSD-2-Clause` | Official Trusted Publishing binary; exact hash match |
| `protobuf` | 7.35.1 | `protobuf-7.35.1-py3-none-any.whl` — `https://files.pythonhosted.org/packages/19/c7/5f7c636ec43e0c545e28d1f1db71990108306f7bdcb89f069ba97e428e7f/protobuf-7.35.1-py3-none-any.whl` | `4bc97768d8fe4ad6743c8a19403e314511ed9f6d13205b687e52421c023ac1b9` | 3-Clause BSD License | Official binary; exact hash match |

All dependency releases were stable, non-yanked, compatible with Python 3.12, and satisfied the declared version constraints. No source distribution, compiler, unsigned executable installer, dependency substitution, upgrade workaround, downgrade workaround, or optional extra was used.

### Installer tooling

The environment also contains `pip==25.0.1`, installed by Python 3.12.13's standard `venv`/`ensurepip` bootstrap. It is installer tooling rather than a Piper runtime dependency and was not downloaded or upgraded during L4. No `setuptools` application dependency was installed.

## Installation command controls

The seven exact wheel paths were installed in one local operation using:

- `--no-index`
- `--no-deps`
- `--no-cache-dir`

These controls prevented network resolution, implicit dependency selection, cache substitution, source builds, optional extras, and package-manager retries during installation. Package metadata inventory afterward reported exactly:

- `flatbuffers==25.12.19`
- `numpy==2.5.1`
- `onnxruntime==1.27.0`
- `packaging==26.2`
- `pathvalidate==3.3.1`
- `piper-tts==1.4.2`
- `protobuf==7.35.1`
- bootstrap tooling `pip==25.0.1`

`pip check` was not run. No Piper or application-dependency import or entry point was used for validation; the post-install inventory came only from `pip` package metadata.

## Runtime assets and post-copy verification

Only the exact verified model and matching config were copied. The model card remained in the provenance cache and was not copied into runtime assets.

| Artifact | Source | Destination | Post-copy SHA-256 | Result |
|---|---|---|---|---|
| `en_US-ljspeech-high.onnx` | `C:\ColdTruthLocalTools\piper-provenance-cache\model\en_US-ljspeech-high.onnx` | `C:\ColdTruthLocalTools\piper-1.4.2-assets\en_US-ljspeech-high.onnx` | `5d4f08ba6a2a48c44592eed3ce56bf85e9de3dd4e20df90541ae68a8310c029a` | Exact source/destination match |
| `en_US-ljspeech-high.onnx.json` | `C:\ColdTruthLocalTools\piper-provenance-cache\model\en_US-ljspeech-high.onnx.json` | `C:\ColdTruthLocalTools\piper-1.4.2-assets\en_US-ljspeech-high.onnx.json` | `7e1f4634af596d83cca997fb7a931ba80b70f8a316a2655ee69c55365e0ace14` | Exact source/destination match |

The runtime asset directory contains no model card, Lessac file, alternate voice, alternate quality, archive, installer, audio file, or unrelated artifact. Neither copied file was renamed, converted, opened for model inspection, parsed, or loaded.

## Stop-condition checks

Every required stop condition was checked before the affected action:

1. The authorized environment and asset paths did not already exist.
2. The cached Piper wheel existed under the exact approved filename and its SHA-256 still matched L3.
3. Official metadata exposed only the two mandatory Piper dependencies and the four mandatory ONNX Runtime dependencies listed above.
4. Every selected version satisfied its declared constraint and Python version requirement.
5. A compatible official PyPI wheel existed for every dependency.
6. Every wheel was stable and non-yanked.
7. Every package had identifiable license metadata; no missing or ambiguous license blocked installation.
8. Every official source URL and SHA-256 was recorded before download.
9. Every downloaded dependency wheel matched its official SHA-256 before installation.
10. No dependency required source compilation or an executable installer.
11. Installation used only exact local wheel paths with package indexes, dependency resolution, and caches disabled.
12. The model/config source hashes matched L3 before copy.
13. Both runtime destinations were absent before copy.
14. Both post-copy hashes matched their verified source files.
15. No extra runtime asset or unapproved voice was introduced.

No stop condition failed.

## Production isolation

The environment has no credential or configuration link to Cold Truth production:

- no credential, API key, token, endpoint, account, provider configuration, browser state, or environment variable was read, copied, written, or linked;
- no vault, production script, case file, media folder, upload configuration, or publishing configuration was copied or referenced;
- no activation hook or production adapter was created;
- no cloud, API, provider, MCP, ElevenLabs, browser, or account route was configured;
- the environment and assets live only under their two authorized `C:\ColdTruthLocalTools` paths.

## Validation

### L2 focused suite

Result: **16/16 passed**

L2 remains a fake-only adapter contract. The new environment is not connected to L2 and was not invoked by the tests.

### K1 focused suite

Result: **14/14 passed**

Kokoro remains frozen, blocked, fake-only, and untouched.

### C1–C8o offline regression

| Suite | Result |
|---|---:|
| C1 | 19/19 passed |
| C2 | 13/13 passed |
| C3 | 6/6 passed |
| C4 | 18/18 passed |
| C5 | 16/16 passed |
| C6 | 18/18 passed |
| C7 | 19/19 passed |
| C8a | 16/16 passed |
| C8b | 12/12 passed |
| C8c | 16/16 passed |
| C8d | 12/12 passed |
| C8e | 12/12 passed |
| C8f/C8g | 18/18 passed |
| C8h | 16/16 passed |
| C8i/C8j | 17/17 passed |
| C8m | 18/18 passed |
| C8n | 9/9 passed |
| C8o | 11/11 passed |

C1–C8o result: **266/266 passed**  
L2 + K1 + C1–C8o result: **296/296 passed**

## Files and directories created or changed

Repository:

- Created `automation/PHASE_L4_PIPER_ISOLATED_ENVIRONMENT_REPORT.md`

External isolated tooling:

- Created `C:\ColdTruthLocalTools\piper-1.4.2-venv\` through standard Python `venv` creation.
- Created `C:\ColdTruthLocalTools\piper-1.4.2-venv\wheelhouse\` containing exactly the six verified mandatory dependency wheels listed in this report.
- Installed exactly the seven locked application packages and bundled `pip` inventory listed above into that environment.
- Created `C:\ColdTruthLocalTools\piper-1.4.2-assets\`.
- Created `C:\ColdTruthLocalTools\piper-1.4.2-assets\en_US-ljspeech-high.onnx`.
- Created `C:\ColdTruthLocalTools\piper-1.4.2-assets\en_US-ljspeech-high.onnx.json`.

The L3 provenance cache was read only and unchanged. No other persistent project, configuration, authorization, production, or media file was created or changed.

## State confirmation

- Piper environment created: yes, only at the authorized isolated path
- Exact Piper package installed: yes, from the cached attested wheel
- Mandatory dependencies installed: yes, exact binary lock above
- Piper, ONNX Runtime, or another installed dependency imported: no
- Piper command, binary, CLI, entry point, demo, server, or test executed: no
- Model or config loaded, parsed, inspected for tensor shape, or selected at runtime: no
- Text processed or supplied to a TTS runtime: no
- Inference or synthesis performed: no
- WAV, MP3, PCM, waveform, spectrogram, or media/audio artifact created: no
- Provider, API, MCP, cloud, browser, or account activity: no
- Credential, environment-variable, API-key, token, endpoint, login, or provider-config access: no
- Authorization created, consumed, inspected, validated, or changed: no
- Other Piper voice/model, including Lessac, downloaded, copied, or installed: no
- Voicebox touched: no
- Frozen Kokoro environment/cache touched: no
- ElevenLabs MCP or direct ElevenLabs route invoked: no
- Codebase Memory indexing/watch enabled: no
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`
- C4 approval created or consumed: no
- Rendering, upload, scheduling, publishing, or production activity: none
- Publishing and real-production modes remain disabled

## Proposed L5 boundary

Only after separate human authorization, L5 may perform a read-only local runtime health verification limited to:

1. Importing the exact installed Piper and ONNX Runtime packages to confirm import health.
2. Confirming the exact model and config files are present at their verified paths.
3. Performing a bounded model-file presence/shape compatibility check if it can be done without text input or inference.
4. Recording versions and safe health status.

L5 must still prohibit text input, voice synthesis, inference output, model narration, WAV/MP3/PCM creation, audio processing, provider activity, production integration, and publishing.

Remaining blocker: human review of L4, followed by a separate explicit L5 authorization.

STOP FOR HUMAN REVIEW.
