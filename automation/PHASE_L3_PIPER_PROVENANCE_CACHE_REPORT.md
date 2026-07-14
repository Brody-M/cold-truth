# Cold Truth — L3 Piper Provenance Cache Report

Date: 2026-07-13  
Phase: L3 — download and provenance verification only  
Outcome: **READY FOR L4 ENVIRONMENT INSTALL REVIEW**

## Scope completed

An isolated, non-executable provenance cache was created outside the repository for exactly:

- Piper distribution: `piper-tts==1.4.2`, Windows x86-64 CPython 3.9+ ABI3 wheel
- Voice/model: `en_US-ljspeech-high`
- Matching model configuration: `en_US-ljspeech-high.onnx.json`
- Exact voice model card: `MODEL_CARD`

No other wheel, model, voice, dependency, installer, repository, binary, or evidence artifact was downloaded. In particular, no Lessac artifact was downloaded.

## Quarantine cache

| Category | Local cache directory |
|---|---|
| Wheel | `C:\ColdTruthLocalTools\piper-provenance-cache\wheel` |
| Model and config | `C:\ColdTruthLocalTools\piper-provenance-cache\model` |
| Evidence | `C:\ColdTruthLocalTools\piper-provenance-cache\evidence` |

The cache contains exactly four files:

1. `wheel\piper_tts-1.4.2-cp39-abi3-win_amd64.whl`
2. `model\en_US-ljspeech-high.onnx`
3. `model\en_US-ljspeech-high.onnx.json`
4. `evidence\MODEL_CARD`

## Piper wheel identity and provenance

| Field | Verified value |
|---|---|
| Package/version | `piper-tts==1.4.2` |
| Distribution filename | `piper_tts-1.4.2-cp39-abi3-win_amd64.whl` |
| Platform tags | CPython 3.9+ ABI3; Windows x86-64 |
| Official source | `https://files.pythonhosted.org/packages/c5/5a/fda959ca07554a8ec3e380b168e79fff16f3020f4956c356a613616c1994/piper_tts-1.4.2-cp39-abi3-win_amd64.whl` |
| Official release metadata | `https://pypi.org/project/piper-tts/1.4.2/` |
| Local path | `C:\ColdTruthLocalTools\piper-provenance-cache\wheel\piper_tts-1.4.2-cp39-abi3-win_amd64.whl` |
| File size | 13,831,944 bytes |
| Official SHA-256 | `9c4a3a11f5889ea9d0df4414dce2bd9bee5ce7d9cf604c8fd5e307441d4c031f` |
| Local SHA-256 | `9c4a3a11f5889ea9d0df4414dce2bd9bee5ce7d9cf604c8fd5e307441d4c031f` |
| Hash result | Exact match |

Official PyPI metadata marks this wheel as uploaded with Trusted Publishing and supplies a publish attestation with:

- in-toto statement type: `https://in-toto.io/Statement/v1`
- predicate type: `https://docs.pypi.org/attestations/publish/v1`
- attested subject name: `piper_tts-1.4.2-cp39-abi3-win_amd64.whl`
- attested subject digest: `9c4a3a11f5889ea9d0df4414dce2bd9bee5ce7d9cf604c8fd5e307441d4c031f`
- publisher workflow: `publish.yml` in `OHF-Voice/piper1-gpl`
- source revision: `d6975e21a440c0d8b6e5fb7c41027409af13d44d`
- source tag: `refs/tags/v1.4.2`
- Sigstore transparency entry: `1219636071`

Result: **official PyPI filename, SHA-256, Trusted Publishing record, and attested subject digest all agree with the quarantined wheel**.

## Exact model, configuration, and model-card verification

The fixed official source is the `rhasspy/piper-voices` repository at tag `v1.0.0`, path `en/en_US/ljspeech/high/`:

`https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0/en/en_US/ljspeech/high`

| Artifact | Official source URL | Local quarantine path | Bytes | Local SHA-256 | Official comparison |
|---|---|---|---:|---|---|
| `en_US-ljspeech-high.onnx` | `https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ljspeech/high/en_US-ljspeech-high.onnx` | `C:\ColdTruthLocalTools\piper-provenance-cache\model\en_US-ljspeech-high.onnx` | 114,199,011 | `5d4f08ba6a2a48c44592eed3ce56bf85e9de3dd4e20df90541ae68a8310c029a` | Exact SHA-256 match to the official Hugging Face Xet pointer; official index MD5 `dad093b5d2cff6a5fda99883ceda09d1` also matches locally. |
| `en_US-ljspeech-high.onnx.json` | `https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ljspeech/high/en_US-ljspeech-high.onnx.json` | `C:\ColdTruthLocalTools\piper-provenance-cache\model\en_US-ljspeech-high.onnx.json` | 4,970 | `7e1f4634af596d83cca997fb7a931ba80b70f8a316a2655ee69c55365e0ace14` | No official SHA-256 is published for this small Git file. Official index size 4,970 and MD5 `de98fc398ddead60fb82d93bfafb3ad1` both match locally. |
| `MODEL_CARD` | `https://huggingface.co/rhasspy/piper-voices/raw/v1.0.0/en/en_US/ljspeech/high/MODEL_CARD` | `C:\ColdTruthLocalTools\piper-provenance-cache\evidence\MODEL_CARD` | 515 | `fbdb9c09bd33e73f6876ba48fc2eeea120b9984d07763bfa21b3c8192fd4ba86` | No official SHA-256 is published for this small Git file. Official index size 515 and MD5 `59322a9a8d2c0e556f0be1171cd54ea7` both match locally. |

The official model tree labels the directory `ljspeech/high`, the model filename and configuration filename both identify `en_US-ljspeech-high`, and the model card heading is `Model card for ljspeech (high)`. The matching configuration declares dataset `ljspeech`, locale `en_US`, one speaker, 22,050 Hz audio, and `quality: high`.

The model card separately says `Quality: medium` and describes training on medium-quality settings. This is a documentation/training-description inconsistency inside the exact high-artifact model card, not an artifact-identity mismatch: the fixed repository path, model name, configuration name, configuration quality field, size, and published hashes all bind the downloaded pair to `en_US-ljspeech-high`. It should remain visible during L4 review.

## License and provenance status

### Piper code/wheel

- PyPI metadata declares `GPL-3.0-or-later` for `piper-tts 1.4.2`.
- The exact Windows wheel is bound to the official `OHF-Voice/piper1-gpl` release by PyPI Trusted Publishing and the publish attestation described above.
- Status: **verified for provenance review; GPL obligations remain applicable to use and distribution**.

### Exact model

- The exact `v1.0.0` model card declares the LJSpeech dataset and `License: public domain` for this voice model.
- The hosting repository is labeled MIT, while the per-model card supplies the model-specific public-domain statement.
- The fixed path, filenames, model/config hashes, and model card bind the evidence to `en_US-ljspeech-high`.
- Status: **verified for L4 install review**.

### LJSpeech source data

- Model-card dataset link: `https://keithito.com/LJ-Speech-Dataset/`
- The official dataset page says LJSpeech is a public-domain speech dataset containing 13,100 clips from one speaker.
- It states that the source texts and LibriVox recordings are public domain and that there are no restrictions on use in the United States; it also identifies the recordings as Linda Johnson's and says the text, audio, and annotations are public domain.
- Status: **official dataset provenance and public-domain statement confirmed**.

### Residual publicity/personality-rights issue

Copyright/public-domain status does not itself prove a worldwide waiver of publicity, personality, endorsement, or false-association rights connected to an identifiable speaker. The source identifies Linda Johnson as the recorded speaker, and no separate worldwide personality-rights release was found in the model card or dataset page.

This does not block isolated L4 environment-install review, but it remains an unresolved release-use caution. Future use must not market the voice as Linda Johnson, imply endorsement, or imitate a real person's identity, and any production use still requires its own human approval and legal/risk review.

## Verification method and safety

- Exact official URLs and published identities were checked before each download.
- Files were downloaded directly to the three approved quarantine directories.
- Local SHA-256 was computed for all four files.
- Published SHA-256 was compared where available; official index size/MD5 was additionally compared for all three voice-repository artifacts.
- The wheel was not opened, unpacked, installed, imported, or executed.
- The ONNX model was not loaded, inspected for executable behavior, or used for inference.
- The JSON configuration was not opened, parsed, imported, or loaded locally.
- No model downloader, Piper CLI, package manager, virtual environment, server, demo, synthesis command, or audio tool was used.

## Validation

### L2 focused suite

Command:

`C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe test_l2_piper_local_adapter_contract.py`

Result: **16/16 passed**

### K1 focused suite

Command:

`C:\Users\brody\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe test_k1_kokoro_local_adapter_contract.py`

Result: **14/14 passed**

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

## Files created or changed

Repository:

- Created `automation/PHASE_L3_PIPER_PROVENANCE_CACHE_REPORT.md`

External quarantine cache:

- Created `C:\ColdTruthLocalTools\piper-provenance-cache\wheel\piper_tts-1.4.2-cp39-abi3-win_amd64.whl`
- Created `C:\ColdTruthLocalTools\piper-provenance-cache\model\en_US-ljspeech-high.onnx`
- Created `C:\ColdTruthLocalTools\piper-provenance-cache\model\en_US-ljspeech-high.onnx.json`
- Created `C:\ColdTruthLocalTools\piper-provenance-cache\evidence\MODEL_CARD`

No other persistent file was created or changed by L3.

## State confirmation

- Piper, ONNX Runtime, or any dependency installed: no
- Virtual environment created or modified: no
- Downloaded wheel/model/config executed, imported, unpacked, parsed, or loaded: no
- Model inference, voice selection at runtime, synthesis, server, CLI, or provider call: no
- WAV, MP3, PCM, waveform, spectrogram, or other media/audio artifact created: no
- Credentials, API keys, environment variables, provider configuration, browser/account data, or secrets accessed: no
- Authorization created, consumed, inspected, validated, or changed: no
- Any unapproved Piper voice/model, including Lessac, downloaded: no
- Frozen Kokoro environment/cache touched: no
- Voicebox installed or touched: no
- ElevenLabs MCP or direct ElevenLabs route invoked: no
- Codebase Memory indexing/watch enabled: no
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`
- C4 approval created or consumed: no
- Rendering, upload, scheduling, publishing, or production activity: none
- Publishing and real-production modes remain disabled

## Conclusion

**READY FOR L4 ENVIRONMENT INSTALL REVIEW**

Proposed L4 scope, only after separate human authorization:

1. Create an isolated Piper virtual environment.
2. Install only the exact cached, attested `piper_tts-1.4.2-cp39-abi3-win_amd64.whl` and separately locked dependencies.
3. Copy or reference only the verified cached `en_US-ljspeech-high` model and matching configuration.
4. Preserve the model-card evidence and the unresolved publicity/personality-rights caution.
5. Do not load the model, run inference, synthesize text, or generate audio during L4.

Remaining blocker: human review of this L3 cache and report, followed by a separate L4 authorization.

STOP FOR HUMAN REVIEW.
