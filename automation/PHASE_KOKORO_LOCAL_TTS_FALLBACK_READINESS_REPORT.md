# Cold Truth — Kokoro Local TTS Fallback Readiness

Date: 2026-07-13
Status: design only; no installation, model download, execution, or audio generation

## Decision

No Voicebox v0.5.0 distribution route meets the approved safe-install rule.

The official release offers an unsigned NSIS setup executable and updater artifacts, but no Authenticode-signed MSI/MSIX, no documented portable Windows application, and no official Windows package-manager installation. Official source-build instructions exist, but a source build is outside this authorization and is not a signed or portable release route.

Voicebox remains uninstalled and unlaunched. Kokoro is the recommended fallback candidate for a future, separately authorized local-TTS evaluation.

## Voicebox v0.5.0 distribution inspection

Official source: <https://github.com/jamiepine/voicebox/releases/tag/v0.5.0>

Windows-relevant assets and methods found:

- `Voicebox_0.5.0_x64-setup.exe` — 541,911,942 bytes; product/file version `0.5.0`; SHA-256 `eaf5410e77946f3a76388270112bfc72925dc9d4c305b891ba600b583bc8b3b8`; Windows Authenticode status `NotSigned`; no company name or signer certificate in static metadata.
- `Voicebox_0.5.0_x64-setup.exe.sig` — detached Tauri updater-signature artifact. The Voicebox release does not document an end-user verification command or public-key workflow that converts this into Windows Authenticode trust.
- `Voicebox_0.5.0_x64-setup.nsis.zip` — NSIS updater bundle. It is not documented by Voicebox as a portable application and therefore is not treated as a portable install route.
- `latest.json` — updater metadata, not a Windows installer.
- `voicebox-server-cuda.tar.gz` and `cuda-libs-cu128-v1.tar.gz` — backend/runtime assets, not standalone verified Voicebox desktop installation routes.
- Source-based Windows build — official repository documents `just setup`, `just build`, and `just build-local`; this requires development dependencies and produces a new local installer. It was not run and does not satisfy this task's signed/portable requirement.

Not found in the official v0.5.0 release or documentation:

- Authenticode-signed MSI or MSIX
- Documented portable Windows ZIP/application
- Official Winget, Chocolatey, or Scoop package command
- Published Windows code-signing certificate chain
- Documented end-user verification procedure beyond published GitHub asset hashes and Tauri updater artifacts

The repository README labels its Windows link “Download MSI,” but the actual v0.5.0 Windows application asset is the unsigned `x64-setup.exe`; there is no MSI asset in the release.

## Recommended official Kokoro installation approach

Official sources:

- Inference library: <https://github.com/hexgrad/kokoro>
- Official PyPI package: <https://pypi.org/project/kokoro/>
- Official model and voice files: <https://huggingface.co/hexgrad/Kokoro-82M>

For a future authorized Windows installation, use a dedicated local Python virtual environment and pin the official Hexgrad package rather than installing into a global Python environment. The proposed approach is:

1. Select a supported 64-bit Python version, preferably Python 3.11 or 3.12.
2. Create a project-isolated virtual environment outside production media directories.
3. Install a human-approved, pinned release of the official `kokoro` package and `soundfile`.
4. Install the official Windows x64 `espeak-ng` MSI only if separately reviewed and authorized; Kokoro documents it as the English out-of-dictionary phoneme fallback.
5. Download only a pinned official `hexgrad/Kokoro-82M` revision and the specifically approved built-in English voicepacks.
6. Verify recorded hashes before any model load.

No part of this approach was executed in this phase.

## Runtime and dependency planning

### Python and packages

The current official `hexgrad/kokoro` project metadata declares:

- Python: `>=3.10, <3.14`
- `huggingface_hub`
- `loguru`
- `misaki[en]>=0.9.4`
- `numpy`
- `torch`
- `transformers`

The official example also uses `soundfile` to write 24 kHz WAV output. English pipelines use Misaki with an espeak-ng fallback.

### Model and storage

- Kokoro v1.0 model weights: approximately 327 MB.
- Published voicepack directory: approximately 28.3 MB for all voices.
- One voicepack: approximately 523 KB.
- Model plus all voicepacks: approximately 356 MB before package/runtime caches.

Planning estimate, not a tested requirement: reserve at least 3–5 GB for a CPU-only Python environment, PyTorch, Transformers, model files, caches, and temporary installation space. A CUDA-enabled PyTorch environment can require several additional gigabytes. Exact storage must be measured after a separately authorized pinned installation.

### CPU, GPU, and RAM

- A discrete GPU is optional; the official project describes Kokoro as an 82-million-parameter model and supports a CPU path through PyTorch.
- Derived weight-memory floor: roughly 327 MB for the published FP32 model file, with additional runtime tensors, phonemization, Python, and output buffers.
- Conservative planning estimate: at least 4 GB of free system RAM for isolated CPU inference, with 8 GB free preferred for long-form stability and testing.
- If GPU acceleration is later evaluated, plan for at least 1–2 GB of free VRAM for this model plus framework overhead, but treat this as an estimate until measured on the actual pinned runtime.

No local performance, RAM, VRAM, or hardware suitability test has occurred.

## Built-in narration voice candidates

Evaluate only built-in, unchanged English voicepacks. Do not blend voices or create derived voice identities during the first test.

Recommended audition order:

1. `af_heart` — official example/default candidate and the only American female voice given an overall `A` grade in the official voice table. First choice for a neutral, calm narration audition.
2. `af_bella` — American female, official overall grade `A-`, with the strongest documented English training-duration band among the highest-quality choices.
3. `bf_emma` — British female, official overall grade `B-`; useful only if a British delivery fits the channel after human audition.
4. `af_nicole` — American female, official overall grade `B-`; secondary audition candidate.

These are candidates, not approvals. Voice selection requires a separately authorized synthetic-text audition and Brody's explicit approval. No real-case text may be used for the first evaluation.

## License and commercial-use boundary

- The official `hexgrad/kokoro` inference repository is Apache-2.0.
- The official `hexgrad/Kokoro-82M` model card labels the weights Apache-2.0 and states that they can be deployed in production and personal projects.
- The English voicepack files are distributed inside that Apache-2.0 model repository, but the official voice table does not provide full source/provenance detail for every English voicepack.
- Some non-English voices explicitly identify Creative Commons attribution sources. Those voices are outside the proposed English narration evaluation.

Before monetized use, retain the exact package/model revision, license files, model-card snapshot, selected voice filename and hash, and any required NOTICE/attribution. Confirm that the selected English voicepack has no separate terms and obtain human/legal acceptance of training-data provenance and any voice/publicity-right risk.

Therefore:

- Apache-2.0 software/model commercial-use permission: documented.
- Complete voicepack provenance and publicity/personality-right clearance for a monetized channel: **unresolved and requires human review before production use**.

## Future Cold Truth architecture

`approved script -> isolated local Kokoro adapter -> exactly one bounded WAV/MP3 output -> assembly preview -> Brody approval`

The adapter must not replace or weaken the existing script and assembly gates.

## Required controls

- No automated retries
- No queue replay or crash regeneration
- No auto-chunking unless separately authorized
- No voice cloning
- No voice blending in the initial evaluation
- No text rewriting or LLM personality layer
- No effects or post-processing unless separately authorized
- Exactly one requested output
- Exclusive-create destination only
- No overwrite, copy, rename, cleanup, alternate output, or fallback
- Pin package, model revision, voice file, sample rate, speed, and output format
- Fail closed on missing dependencies, unsafe paths, duration anomalies, or unexpected additional files
- Record a sanitized manifest without text leakage beyond the approved synthetic fixture

## Proposed first offline-only adapter phase

Create a new isolated phase, tentatively `K1 — Kokoro Adapter Contract, Fake Transport Only`.

The phase should:

1. Define a small local synthesis request contract containing approved text reference, fixed voice name, speed, sample rate, output format, and exact destination.
2. Inject a fake local synthesis transport; do not import Kokoro, PyTorch, Hugging Face, or audio libraries.
3. Prove exactly-once invocation and no retry, queue, fallback, or chunking.
4. Enforce exclusive-create output and a single allowed artifact path.
5. Reject voice cloning, voice tensors supplied by callers, voice blending, personality/rewrite fields, effects, and arbitrary model revisions.
6. Validate fail-closed behavior for existing targets, unsafe parents, links/reparse points, extra artifacts, and malformed fake responses.
7. Produce sanitized immutable test records with no credentials, environment values, real-case text, or audio.
8. Run offline regression tests only.

A later phase may replace the fake transport with a bounded local Kokoro process only after package/model installation, licensing review, and a new explicit human authorization.

## Human gates and separate authorizations

Existing gates remain unchanged:

1. The reverse outline and full script must receive paired human approval before `Script_Final.md` or narration work.
2. Generated narration must pass the current duration/preflight rules.
3. Brody must approve the assembled preview before rendering or uploading.

Separate future authorizations are required for each of the following:

- Installing the pinned Kokoro runtime and dependencies
- Downloading the model and selected built-in voice files
- Running the first fake-text local generation test
- Connecting a real local Kokoro adapter to any production pipeline
- Generating narration from any approved real-case script

## Safety confirmation

- Voicebox installer or binary executed: no
- Voicebox installed or launched: no
- Kokoro installed or imported: no
- Model or voice files downloaded: no
- Model execution or local synthesis: no
- Audio or media created: no
- TTS provider/API/MCP call: no
- Credentials, environment values, account data, or API keys accessed: no
- Existing C8o or historical authorization/audit contents accessed or changed: no
- C3 remains exactly `AWAITING_SCRIPT_APPROVAL`
- No C4 approval was created or consumed
- Rendering, upload, scheduling, publishing, and real production remain disabled
