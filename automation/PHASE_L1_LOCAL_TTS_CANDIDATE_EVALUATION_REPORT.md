# Cold Truth — L1 Local TTS Candidate Evaluation

Date: 2026-07-13  
Phase: L1 — read-only license, provenance, maintenance, and Windows-feasibility research  
Status: **ONE CANDIDATE ELIGIBLE FOR A CONTROLLED READINESS PHASE**

## Scope and decision rule

This review evaluates local, offline English TTS candidates using only official project repositories, official package registries, official model-hosting pages, and official dataset sources. No package, model, voice, binary, installer, or source archive was downloaded. Nothing was installed, imported, executed, benchmarked, or used to create audio.

Eligibility requires all of the following:

- A maintained official implementation with a documented Windows route.
- Clear code license.
- Clear model/checkpoint license.
- Officially documented voice-training source and usable terms for monetized narration.
- No compulsory cloud account, API key, or provider charge.
- A feasible bounded local invocation compatible with Cold Truth's no-retry and no-auto-publish rules.

## Comparison table

| Candidate | Current official status | Code license | Model / voice evidence | Commercial status | Windows / CPU profile | Cold Truth fit | Recommendation |
|---|---|---|---|---|---|---|---|
| **Piper 1.4.2 + `en_US-ljspeech-high`** | Open Home Foundation successor; v1.4.2 released 2026-04-02 | GPL-3.0-or-later | Piper voice repository marked MIT; voice model card identifies LJSpeech; source dataset says text, recordings, and annotations are public domain with no use restrictions | **Clear**, subject to GPL obligations for distributed engine code | Trusted-published CPython 3.9+ Windows x86-64 wheel; Python environment; no local compilation; CPU-first; GPU optional | One bounded local WAV, fixed voice, no cloning/cloud/retry required | **eligible for controlled readiness phase** |
| **Coqui TTS 0.22.0 / XTTS-v2 2.0.3** | Last official code release 2023-12-12; original project no longer provides a current commercial licensing route | MPL-2.0 | XTTS-v2 checkpoint uses CPML 1.0.0 | **Prohibited for monetized use under the published model license** | Python/PyTorch; Windows possible; CPU possible but heavy; GPU preferred; local WAV | Voice-cloning design conflicts with the no-cloning rule, and outputs are non-commercial | **reject** |
| **StyleTTS2** | Research repository; no official GitHub releases | MIT | Official LJSpeech and LibriTTS checkpoint repositories have no model cards or checkpoint-license declarations | **Unclear** | Python/PyTorch; Windows instructions emphasize CUDA; phonemizer/eSpeak dependency; CPU inference possible but operationally complex | Can write local audio, but checkpoint terms and speaker-permission conditions are not sufficiently fixed for automation | **needs legal/provenance review** |
| **Parler-TTS Mini v1** | No GitHub releases; principal English checkpoint last updated 2024-11-25 | Apache-2.0 | Checkpoint Apache-2.0; official training datasets documented as CC BY 4.0/public domain | Model copyright status is clear; residual speaker/publicity concerns remain | Python/PyTorch source install; 0.9B/3.51 GB checkpoint; CPU path exists but is likely impractical for repeated 8–10 minute student-desktop narration; GPU optimizations dominate official guidance | Can produce local WAV and avoid cloning with generic descriptions, but generation is stochastic and named-speaker behavior remains available | **reject for the current readiness phase** |

Only Piper with the specifically identified LJSpeech model passes L1. No other Piper voice is implicitly approved.

## 1. Piper 1.4.2 with `en_US-ljspeech-high`

### Official sources and maintenance

- Official successor repository: <https://github.com/OHF-Voice/piper1-gpl>
- Official releases: <https://github.com/OHF-Voice/piper1-gpl/releases>
- Official package registry: <https://pypi.org/project/piper-tts/>
- Latest release reviewed: `v1.4.2`, released 2026-04-02 from official commit `d6975e21a440c0d8b6e5fb7c41027409af13d44d`
- Official voice documentation: <https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md>
- Official voice repository: <https://huggingface.co/rhasspy/piper-voices>
- Fixed voice-model release tree: <https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0/en/en_US/ljspeech/high>
- Fixed voice model card: <https://huggingface.co/rhasspy/piper-voices/blob/v1.0.0/en/en_US/ljspeech/high/MODEL_CARD>

Piper is actively release-maintained by the Open Home Foundation successor organization. PyPI publishes a CPython 3.9+ Windows x86-64 wheel for 1.4.2 through Trusted Publishing and binds it to the official `v1.4.2` tag. The wheel is 13.8 MB and its published SHA-256 is `9c4a3a11f5889ea9d0df4414dce2bd9bee5ce7d9cf604c8fd5e307441d4c031f`.

### Licensing and provenance

- Engine code: GPL-3.0-or-later.
- Voice repository/model hosting classification: MIT.
- Model: `en_US-ljspeech-high`, single-speaker U.S. English ONNX model, trained from scratch on LJSpeech.
- Training data: LJSpeech 1.1.
- Official LJSpeech source: <https://keithito.com/LJ-Speech-Dataset/>
- Dataset provenance: 13,100 clips, approximately 24 hours, recorded by Linda Johnson for LibriVox and aligned by Keith Ito.
- Dataset terms: the source states that the text, audio, and annotations are public domain and have no use restrictions.

Commercial-use status: **clear for this specific engine/model/data combination**, provided any distribution of Piper itself complies with GPL-3.0-or-later. Merely being free of charge does not remove those obligations.

Voice/publicity assessment: the underlying reader is identified and the source expressly places the recordings in the public domain. That is materially stronger provenance than an anonymous or undocumented voicepack. A residual jurisdiction-specific publicity/personality-right question can never be eliminated by a copyright label alone, so Cold Truth should not market the output as Linda Johnson, imply endorsement, or imitate a living public persona. This residual caution does not block a controlled technical readiness phase.

### Important excluded Piper voices

The commonly demonstrated `lessac` voice is **not approved**. Its model card links to the Blizzard 2013 Lessac/Voice Factory data, whose official license is research-only and expressly excludes commercial voice-synthesis use:

- Model card: <https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/lessac/medium/MODEL_CARD>
- Source-data terms: <https://www.cstr.ed.ac.uk/projects/blizzard/2013/lessac_blizzard2013/license.html>

No inference may be made from Piper's general voice-repository MIT label that every underlying voice dataset is commercially usable. The project itself instructs users to review each voice model card.

### Windows and runtime feasibility

- Installation route: official PyPI wheel into an isolated Python environment.
- Unsigned installer: no standalone installer is required.
- Custom local compilation: no; use the official attested Windows wheel.
- Native component: the official wheel embeds eSpeak NG support under the engine's GPL-3.0-or-later distribution model. Its future readiness phase must still pin and verify the exact wheel and included notices before execution.
- Python environment: yes, Python 3.9 or newer.
- GPU: no. CUDA is optional through `onnxruntime-gpu`.
- Cloud/API/account/key: none after obtaining the approved local artifacts.
- CPU-only student desktop: strong fit; Piper is designed as a fast local engine and uses compact ONNX voices.

### Narration quality and output behavior

The chosen folder is named `high`, although its own model card describes the voice quality as `medium`. Expected quality is clear and intelligible but less natural and expressive than current premium cloud narration. It may suit calm factual delivery, but a later human listening gate must decide whether it meets the Cold Truth brand.

The official CLI and Python API write WAV directly to a caller-selected local file. Raw streaming output is also supported. A controlled adapter can accept one approved script and one exact destination, issue one synthesis operation, disable retries, reject pre-existing output, and stop after the bounded WAV is written. Fixed parameters and a fixed voice make operation reproducible in configuration; the official documentation does not promise byte-for-byte deterministic synthesis, so a future contract must not claim that stronger property without testing.

Cold Truth fit: **yes**, if L2 hard-locks only `en_US-ljspeech-high`, forbids voice cloning and arbitrary voice downloads, performs no automatic retry, and creates no publish action.

Recommendation: **eligible for controlled readiness phase**.

## 2. Coqui TTS / XTTS-v2

### Official sources

- Code repository: <https://github.com/coqui-ai/TTS>
- Releases: <https://github.com/coqui-ai/TTS/releases>
- XTTS-v2 documentation: <https://github.com/coqui-ai/TTS/blob/dev/docs/source/models/xtts.md>
- Official checkpoint: <https://huggingface.co/coqui/XTTS-v2>
- Version-specific model license: <https://huggingface.co/coqui/XTTS-v2/blob/v2.0.3/LICENSE.txt>

Maintenance status: latest official TTS release `v0.22.0`, dated 2023-12-12. The XTTS-v2 model manifest identifies version 2.0.3.

Code license: MPL-2.0. Model license: Coqui Public Model License 1.0.0.

The CPML grants rights only for non-commercial purposes and states that the model and its outputs are non-commercial. A monetized Cold Truth episode is outside those published terms absent a separate commercial license, and no current official licensing route was verified.

Voice provenance/publicity: XTTS is explicitly a short-reference voice-cloning system. Any use would require rights in the reference voice in addition to model permission. Cold Truth's requested stack must not use voice cloning.

Windows feasibility: Python/PyTorch local inference can write WAV; a GPU is preferred, while CPU operation would be heavy. No cloud account is technically required for local inference, but licensing alone is disqualifying.

Recommendation: **reject**.

## 3. StyleTTS2

### Official sources

- Code repository: <https://github.com/yl4579/StyleTTS2>
- Code license: <https://github.com/yl4579/StyleTTS2/blob/main/LICENSE>
- Releases: <https://github.com/yl4579/StyleTTS2/releases>
- Official LJSpeech checkpoint repository: <https://huggingface.co/yl4579/StyleTTS2-LJSpeech>
- Official LibriTTS checkpoint repository: <https://huggingface.co/yl4579/StyleTTS2-LibriTTS>

Maintenance status: research repository with no formal GitHub releases. The code is MIT-licensed.

Model-license status: **unclear**. Both official checkpoint repositories currently have no model card and expose no model-specific license declaration. The code repository's MIT license cannot automatically be applied to separately hosted weights.

Voice provenance: the README identifies LJSpeech and LibriTTS training sources, but the model repositories do not provide a complete checkpoint license/provenance record. The README also places conditions around public synthesis of voices without speaker permission and describes reference-audio use for the multi-speaker model. That is not sufficiently precise for an automated monetized channel.

Windows feasibility: Python and PyTorch are required. The official instructions describe a CUDA-oriented Windows installation and require a phonemizer/eSpeak path for the demo. CPU inference is mentioned as a possible workaround, but this is not a simple verified Windows release route. Output can be written locally, but no formally released package or bounded production interface is supplied.

Expected narration quality: potentially very high, but quality does not cure missing checkpoint terms or voice-right ambiguity.

Recommendation: **needs legal/provenance review** and is disqualified from L2 under the current decision rule.

## 4. Parler-TTS Mini v1

### Official sources

- Code repository: <https://github.com/huggingface/parler-tts>
- Releases: <https://github.com/huggingface/parler-tts/releases>
- Official model: <https://huggingface.co/parler-tts/parler-tts-mini-v1>
- English MLS dataset: <https://huggingface.co/datasets/parler-tts/mls_eng>
- Filtered LibriTTS-R dataset: <https://huggingface.co/datasets/parler-tts/libritts_r_filtered>
- MLS annotations: <https://huggingface.co/datasets/parler-tts/mls-eng-speaker-descriptions>
- LibriTTS-R annotations: <https://huggingface.co/datasets/parler-tts/libritts-r-filtered-speaker-descriptions>

Maintenance status: no formal GitHub releases. The official model page identifies Mini v1 as a 2024 checkpoint, and the model organization shows its last update on 2024-11-25. This is not a sufficiently current release-maintenance signal for a new 2026 production dependency.

Code license: Apache-2.0. Model license: Apache-2.0. The model card links the training sources and states that the datasets, preprocessing, training code, and weights are public under permissive terms. The official MLS and LibriTTS-R derivatives are identified as CC BY 4.0/public-domain data.

Commercial status: clear at the copyright-license level. Attribution obligations must be retained for CC BY material.

Voice/publicity assessment: the model was trained on thousands of audiobook speakers and offers 34 named speaker controls. The MLS card says the speakers donated voices online and instructs users not to determine their identities. Even without reference-audio cloning, speaker-like output and named-speaker selection create a nontrivial identity/publicity concern. A generic descriptive voice prompt reduces but does not eliminate it.

Windows feasibility: Python/PyTorch source installation from the official repository; no standalone unsigned installer and no compulsory cloud account. The Mini v1 checkpoint is approximately 0.9B parameters and 3.51 GB. Official examples permit `cpu`, but performance documentation focuses on modern GPUs, SDPA, Flash Attention, and compilation. Autoregressive generation requires many decoding steps, making an eight-to-ten-minute CPU-only narration a poor student-desktop fit without a benchmark—which L1 did not perform.

Output: official examples write local WAV. A seed can be fixed, but generation is stochastic and the official project does not claim cross-platform byte determinism. A bounded adapter is conceptually possible, but current maintenance, CPU practicality, and voice-identity risk prevent L2 selection.

Recommendation: **reject for the current readiness phase**.

## Ranking and decision

1. **Piper 1.4.2 + `en_US-ljspeech-high` — eligible for controlled readiness phase.**
2. Parler-TTS Mini v1 — strongest license documentation among the rejected alternatives, but stale release maintenance, CPU cost, and speaker-identity concerns keep it out of L2.
3. StyleTTS2 — high potential quality, but checkpoint licensing and speaker conditions are insufficiently documented.
4. Coqui XTTS-v2 — directly incompatible with monetized use under CPML and built around voice cloning.

Clear winner: **Piper 1.4.2 with only the fixed `en_US-ljspeech-high` voice model**.

## Recommended next phase

Proceed only after human approval to an **L2 candidate-specific offline adapter contract** for Piper. L2 should remain fake-transport/contract-only and must not install or download anything unless a later phase separately authorizes it. The contract should:

- Pin Piper `1.4.2` and its Trusted-Publishing-bound Windows wheel hash.
- Pin the `piper-voices` `v1.0.0` LJSpeech model tree and exact ONNX/config hashes before any later download.
- Permit only `en_US-ljspeech-high`; reject Lessac and every unreviewed voice.
- Require one approved script, one exact WAV destination, exclusive creation, zero retries, no server, no browser, no cloud, no voice cloning, and no publish action.
- Record GPL-3.0-or-later, MIT, and public-domain notices in the run manifest.
- Require a later isolated listening/readiness test before any production consideration.

## “Free” is not the same as commercially safe

A zero-dollar download does not establish commercial permission. Engine code, model weights, training recordings, annotations, and a speaker's identity/publicity interests can each carry different terms. Cold Truth must approve all of those layers, not merely find an open repository or a downloadable checkpoint.

## Activity and state confirmation

- Report created: `automation/PHASE_L1_LOCAL_TTS_CANDIDATE_EVALUATION_REPORT.md`
- Other repository files changed: none
- Package, model, voicepack, binary, installer, or source download: none
- Installation, environment creation/modification, import, compilation, execution, benchmark, inference, local server, or audio generation: none
- Audio or media file created: none
- Browser automation, provider request, API call, credential, API key, environment variable, private configuration, or account access: none
- Authorization created, inspected, consumed, or changed: none
- Frozen Kokoro environment/model cache accessed, imported, executed, repaired, modified, uninstalled, or reused: no
- Voicebox, ElevenLabs, ElevenLabs MCP, or direct ElevenLabs HTTPS evaluated or invoked: no
- K1 real-runtime capability added: no; K1 remains fake-only
- C1–C8o, K1, K2/K2a, Codebase Memory configuration, historical records, approval gates, and production settings changed: no
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`
- C4 approval created or consumed: no
- Rendering, upload, scheduling, publishing, or production activity: none
- Publishing and real-production modes remain disabled

STOP FOR HUMAN REVIEW.
