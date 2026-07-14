# Cold Truth — K2 Kokoro Environment and Provenance Report

Date: 2026-07-13  
Phase: K2 — install/model-download readiness only  
Status: **BLOCKED — transitive dependency license provenance missing**

## Approved sources recorded before installation or download

### Inference package

- Package: `kokoro`
- Pinned version: `0.9.4`
- Maintainer shown by PyPI: `hexgrad`
- Distribution: `kokoro-0.9.4-py3-none-any.whl`
- Official project page: <https://pypi.org/project/kokoro/0.9.4/>
- Official distribution URL: <https://files.pythonhosted.org/packages/ea/cc/75f41633c75224ba820a4533163bc8b070b6bf25416014074c63284c2d4e/kokoro-0.9.4-py3-none-any.whl>
- Official PyPI SHA-256: `a129dc6364a286bd6a92c396e9862459d3d3e45f2c15596ed5a94dcee5789efd`
- Published license: Apache License 2.0
- Python requirement published by PyPI: `>=3.10,<3.13`

The package wheel will be installed first without dependencies. Its packaged dependency metadata will then be inspected locally without importing Kokoro. Each dependency must be identified and approved before installation; any ambiguous package, source, or license stops K2.

The installed wheel declares six direct dependencies. The following conservative, release-era-compatible versions were recorded before dependency installation; only official PyPI binary distributions are permitted:

| Package | Pinned version | Official source | Published license |
|---|---:|---|---|
| `huggingface-hub` | `0.30.2` | <https://pypi.org/project/huggingface-hub/0.30.2/> | Apache License 2.0 |
| `loguru` | `0.7.3` | <https://pypi.org/project/loguru/0.7.3/> | MIT License |
| `misaki[en]` | `0.9.4` | <https://pypi.org/project/misaki/0.9.4/> | Apache License 2.0 |
| `numpy` | `2.2.4` | <https://pypi.org/project/numpy/2.2.4/> | BSD-3-Clause |
| `torch` | `2.6.0` | <https://pypi.org/project/torch/2.6.0/> | BSD-style / published PyTorch license |
| `transformers` | `4.51.3` | <https://pypi.org/project/transformers/4.51.3/> | Apache License 2.0 |

Transitive dependencies may be resolved only from their official PyPI binary-wheel metadata. The final report must enumerate their exact installed versions and published package licenses. No source distribution or source build is approved.

### Base model

- Repository: `hexgrad/Kokoro-82M`
- Pinned repository revision: `f48a184bdc2f5f7c73c5f4c8f9e28a3b0fd0ff0a`
- Asset: `kokoro-v1_0.pth`
- Official source page: <https://huggingface.co/hexgrad/Kokoro-82M/blob/f48a184bdc2f5f7c73c5f4c8f9e28a3b0fd0ff0a/kokoro-v1_0.pth>
- Official download URL: <https://huggingface.co/hexgrad/Kokoro-82M/resolve/f48a184bdc2f5f7c73c5f4c8f9e28a3b0fd0ff0a/kokoro-v1_0.pth?download=true>
- Official published SHA-256: `496dba118d1a58f5f3db2efc88dbdc216e0483fc89fe6e47ee1f2c53f18ad1e4`
- Published size: approximately 327 MB
- Published license: Apache License 2.0
- Safety note: Hugging Face identifies the asset as a PyTorch pickle containing only documented tensor reconstruction imports. K2 may download and hash it but must not deserialize or load it.

The minimum base-model configuration asset is also approved from the same fixed official revision:

- Asset: `config.json`
- Official source URL: <https://huggingface.co/hexgrad/Kokoro-82M/blob/f48a184bdc2f5f7c73c5f4c8f9e28a3b0fd0ff0a/config.json>
- Official download URL: <https://huggingface.co/hexgrad/Kokoro-82M/resolve/f48a184bdc2f5f7c73c5f4c8f9e28a3b0fd0ff0a/config.json?download=true>
- Official checksum: `official checksum not published`
- Published repository license: Apache License 2.0

### Voicepacks

No voicepack is approved for download in K2. The official repository distributes voicepack files under its Apache-2.0 repository license and publishes short hashes and quality/training-duration grades, but it does not provide sufficiently complete per-voice source identity and publicity/personality-right provenance for Cold Truth monetized production review.

Status for every candidate voicepack: `not approved for production pending review`.

Downloaded voicepacks: none. No candidate voice is selected or approved for production.

## Approved local locations

- Virtual environment: `C:\ColdTruthLocalTools\kokoro-venv`
- Model/cache root: `C:\ColdTruthLocalTools\kokoro-model-cache`

## Installation and validation results

### Python and environment

- Base Python executable: `C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
- Base Python version: `3.12.13`
- Isolated virtual environment: `C:\ColdTruthLocalTools\kokoro-venv`
- Environment Python: `C:\ColdTruthLocalTools\kokoro-venv\Scripts\python.exe`
- Dependency consistency check: `No broken requirements found.`
- Kokoro import, model load, voice load, synthesis, and inference: not performed

### Exact installed environment lock

All application dependencies were installed from PyPI binary wheels. No source distribution or source build was used.

```text
addict==2.4.0
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.14.2
attrs==26.1.0
babel==2.18.0
blis==1.3.3
catalogue==2.0.10
certifi==2026.6.17
charset-normalizer==3.4.9
cloudpathlib==0.24.0
colorama==0.4.6
confection==1.3.3
csvw==4.1.0
curated-tokenizers==0.0.9
curated-transformers==0.1.1
cymem==2.0.13
dlinfo==2.0.0
espeakng-loader==0.2.4
filelock==3.29.7
fsspec==2026.6.0
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
huggingface-hub==0.30.2
idna==3.18
isodate==0.7.2
Jinja2==3.1.6
joblib==1.5.3
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
kokoro==0.9.4
language-tags==1.3.1
loguru==0.7.3
markdown-it-py==4.2.0
MarkupSafe==3.0.3
mdurl==0.1.2
misaki==0.9.4
mpmath==1.3.0
murmurhash==1.0.15
networkx==3.6.1
num2words==0.5.6
numpy==2.2.4
packaging==26.2
phonemizer-fork==3.3.2
pip==25.0.1
preshed==3.0.13
pydantic==2.13.4
pydantic_core==2.46.4
Pygments==2.20.0
pyparsing==3.3.2
python-dateutil==2.9.0.post0
PyYAML==6.0.3
rdflib==7.6.0
referencing==0.37.0
regex==2026.7.10
requests==2.34.2
rfc3986==1.5.0
rich==15.0.0
rpds-py==2026.6.3
safetensors==0.8.0
segments==2.4.0
setuptools==83.0.0
shellingham==1.5.4
six==1.17.0
smart_open==8.0.0
spacy==3.8.14
spacy-curated-transformers==0.3.1
spacy-legacy==3.0.12
spacy-loggers==1.0.5
srsly==2.5.3
sympy==1.13.1
termcolor==3.3.0
thinc==8.3.13
tokenizers==0.21.4
torch==2.6.0
tqdm==4.68.4
transformers==4.51.3
typer==0.26.8
typing_extensions==4.16.0
typing-inspection==0.4.2
uritemplate==4.2.0
urllib3==2.7.0
wasabi==1.1.3
weasel==1.0.0
win32_setctime==1.2.0
wrapt==2.2.2
```

The pinned direct dependency license terms are recorded in the pre-install table above. The installed transitive metadata scan found standard published permissive-license declarations across the scanned packages, plus the separately disclosed `num2words==0.5.6` GPLv3-or-later metadata. It then encountered the mandatory stop condition below.

### Mandatory stop condition

`espeakng-loader==0.2.4`, pulled by the official `misaki[en]==0.9.4` dependency declaration, has no `License-Expression`, no `License`, and no license classifier in its installed wheel metadata. Its package-license provenance is therefore missing under the K2 rules.

K2 stopped immediately when this was identified. No repair, retry, uninstall, substitution, alternate package, runtime import, health check, or continued validation was attempted.

### Downloaded base-model assets

| Asset | Cache path | Bytes | SHA-256 result | License |
|---|---|---:|---|---|
| `config.json` | `C:\ColdTruthLocalTools\kokoro-model-cache\config.json` | 2,351 | Local SHA-256 `5abb01e2403b072bf03d04fde160443e209d7a0dad49a423be15196b9b43c17f`; official checksum not published | Apache License 2.0 repository |
| `kokoro-v1_0.pth` | `C:\ColdTruthLocalTools\kokoro-model-cache\kokoro-v1_0.pth` | 327,212,226 | `496dba118d1a58f5f3db2efc88dbdc216e0483fc89fe6e47ee1f2c53f18ad1e4` — exact match to official published SHA-256 | Apache License 2.0 |

The model file was downloaded and hashed only. It was never opened through PyTorch, deserialized, loaded, or used for inference.

Downloaded voicepacks: none. Every candidate remains `not approved for production pending review`, and no voice is selected.

### Required validation status

- K1 focused suite: **not run after K2**, because the K2 provenance stop condition occurred first.
- C1–C8o regression baseline: **not run**, because K1 could not be run after the stop.
- No new combined test total is claimed.

## K3 proposal — blocked pending provenance decision

K3 cannot begin while K2 is blocked. After a separate human-reviewed provenance resolution, a separately authorized K3 may perform a local runtime health check without synthesis, voice selection, model/voicepack loading for inference, or audio/media output.

## Actions that remain prohibited

- Any Kokoro synthesis, inference, pipeline call, demo, sample, notebook, CLI generation, API endpoint, or local server
- Any WAV, MP3, PCM, waveform, spectrogram, or other audio/media creation
- Loading or executing a voicepack for speech generation
- Selecting, approving, cloning, importing, blending, or configuring a production voice
- Connecting a real runtime to K1 or changing K1's fake-only dependencies
- Voicebox or ElevenLabs execution, MCP use, direct provider HTTPS, cloud TTS, browser automation, or external provider calls
- Credential, API-key, environment-variable, private-configuration, account, browser-data, or secret access
- C8o or historical C8/C8n authorization/audit content access or mutation
- Real-case narration, rendering, upload, scheduling, publishing, or production enablement

STOP FOR HUMAN REVIEW after K2 validation.

## Safety and state confirmation

- Actual Kokoro inference or TTS request: not performed
- Kokoro package imported or synthesis method called: no
- Model deserialized or loaded: no
- Voicepack downloaded or loaded: no
- Audio/media artifact created: no
- Voicebox or ElevenLabs route invoked: no
- Provider/API/MCP request made: no
- Credential, API-key, environment-variable, private-configuration, account, browser-data, or secret access: no
- C8o or historical C8/C8n authorization/audit content access: no
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`
- C4 approval created or consumed: no
- Rendering, upload, scheduling, publishing, or production activity: no

Remaining blocker: human review and a separately authorized, provenance-specific resolution for `espeakng-loader==0.2.4`. K3 is not authorized.
