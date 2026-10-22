# VoiceStudio CPU trial — listening review

[[00_START_HERE|Home]] · [[0_ADMIN/PROJECT_DASHBOARD|Queue]] · [[0_ADMIN/VOICESTUDIO_EVALUATION_2026_10_20|Provider assessment]] · [[2_CHANNEL_SYSTEM/NARRATION_VOICE|Production voice history]]

**Current result:** Brody approved the full **9:30.56** processed Mia narration on October21; the [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/preflight.json|audio preflight]] passes. One full request used **1,722 existing credits**; no attempts remain. The separately [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/phase_2_m6_preparation_2026_10_21.json|approved M6 preparation scope]] has produced exact-audio timing, local stock, original cards and verified existing Orbital provenance. The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/M6_Preparation_Handoff|M6 review hub]] records the completed script/rights/timing reviews and next execution scope. Video assembly/rendering, new narration and publishing are outside this grant. Kitten/Bella stays parked. The [[0_ADMIN/MIA_AUDIO_EDIT_2026_10_20|Mia comparison record]] supersedes historical next-action text below.

**Original trial:** two authorized neutral samples generated and technically verified. [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/voicestudio_cpu_trial_approval_2026_10_20.json|neutral-trial approval]] binds the unchanged proposal and the quote “Authorize this CPU voice trial.” [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/voicestudio_cpu_trial_result_2026_10_20.json|measured trial receipt]] records requests, hashes, measurements and limits. This is an internal synthetic voice comparison, not Amy narration or production voice approval. Both trial attempts are used; no automatic retry occurred.

## Listen

[Bella sample](<C:/Youtube Automation Obsidian/voice_samples/voicestudio_trial_01/bella_01.wav>) · [Luna sample](<C:/Youtube Automation Obsidian/voice_samples/voicestudio_trial_01/luna_01.wav>)

Both are PCM 16-bit WAV, 24 kHz, mono, normal speed, with the same neutral 49-word text from the proposal. The output hashes differ. Technical checks do not establish pronunciation, completeness or creative quality.

| Voice | Actual preset ID | Audio duration | Request wall time | Sampled peak backend process-tree RSS |
|---|---|---|---|---|
| Bella | `expr-voice-2-f` | 26.716667 s | 41.203 s | 921.5 MiB |
| Luna | `expr-voice-3-f` | 20.691667 s | 29.187 s | 938.7 MiB |

These two requests took longer than the resulting audio. Bella includes first model-load overhead; this small trial is not a sustained throughput benchmark. RAM figures sample the backend process tree every 250 ms and exclude installation/system memory.

The backend logged **phonemizer word-count mismatch warnings** during both requests. Listen through every sentence, especially “At eight fifteen in the morning,” and check missing or blurred words, pronunciation, calmness and natural pacing. No ASR or subjective listening approval was fabricated. Brody has now tentatively preferred Bella while reporting slow/grainy delivery for both. This is not a quality pass; no further generation fits the exhausted original grant.

## Verified installation and boundaries

- Stable [VoiceStudio Electron v0.5.6](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6), installed under `voice_samples/voicestudio_trial_01/app`. The 214,447,484-byte Windows installer matches SHA-256 `3d7ac1d6b54e7854ca7fff4dda838e402d1c5d31acc9656b1838432e29a97624` in both official release metadata and `SHA256SUMS.txt`.
- The release's bundled bootstrap selects CUDA on Windows. The private runtime instead preserves its frozen dependency versions with CPU PyTorch 2.8.0, torchaudio 2.8.0 and torchvision 0.23.0 wheels. Installed app/backend sources remain unchanged. This is a documented CPU runtime variant, not a claim that the stock GUI bootstrap supports this setup.
- Kitten adapter/library 0.8.1 loads **mini 0.8**, repository revision `c02725660cea441db4c383af69f1f26f5cd00947`. Config, weights and preset file total 81,547,388 bytes; including its model card, 81,548,122 bytes. Weight hashes and Git blob IDs were verified before loading. The model-card metadata says Apache-2.0; app/component notices are retained separately.
- Offline inspection of the exact installed adapter/model reports only `CPUExecutionProvider`, CPU-only torch, and both requested keys in the voice weights. Live `/health` reports 0.5.6/CPU; OpenAPI and actual engine catalog were captured. The post-generation catalog reports Kitten loaded/effective CPU but leaves its actual-provider field null; that field is not treated as independent provider proof.
- HF/Transformers offline flags stay enabled during validation/generation. No additional speech/ASR/AudioSeal weights were downloaded. The release-pinned Kitten phonemizer dependency chain includes packaged `en-core-web-sm` 3.8.0 NLP data (~12.2 MiB wheel); this is disclosed rather than called another TTS model. Component license metadata/notices are indexed in the trial folder. Production rights review remains open.
- Current directly attributable trial file allocation is conservatively estimated at **5.467 GiB**, counting hardlinks once and rounding files to 4 KiB, within the 10 GiB ceiling. An initial whole-drive guard stopped dependency installation; whole-drive free-space changes exceeded trial file sizes and include unattributed concurrent/system activity. The resumed install reused its cache with hardlinks and one download/install at a time. Historical whole-drive peak attribution cannot be certified; small installer registry/shortcut and directory metadata are excluded. See the receipt for raw readings and accounting limits.
- No paid service, cloud synthesis, cloning, Amy episode narration, visuals, rendering or publishing occurred. The historical ElevenLabs grant remains held and unused. Amy's exact reviewed script/outline/final binding still passes.

The stable installed backend was exercised through its local API. **The desktop GUI and its first-run settings were not validated.** `automation/start_voicestudio_cpu_trial.py` is a prepared, untested launcher using the supported backend-command override; it submits no generation. Do not use the stock CUDA bootstrap or treat the launcher as production certification.

## Next in the maintained plan

**Historical refinement checkpoint:** Bella was tentatively preferred and one faster take was separately authorized. That refinement is complete and its delivery was subsequently rejected. All local synthesis grants are exhausted. Brody authorized one neutral Mia comparison at speed 1.0; the 20.57-second sample is complete and provider history confirms 61 credits used (276 quoted, 400 cap). Brody finds it pretty good but reports loud P sounds/peaks, and explicitly requested the vault Editor agent to filter the existing file. That offline edit is complete and technically verified; listening acceptance is pending. See [[0_ADMIN/MIA_AUDIO_EDIT_2026_10_20|Mia sample audio edit]]. Kitten/Bella remains parked. The full Amy narration grant stays held; no episode request has run.

## Pacing and texture diagnosis after listening

Bella's 49-word sample runs about **110 words/minute including pauses**; Luna is about **142 words/minute**, although Brody perceived both as slow. A threshold-based FFmpeg check found about **3.50 seconds** of Bella audio below -40 dBFS in intervals of at least 250 ms, including edges. This cannot establish missing speech or justify automatically cutting natural pauses.

The files are uncompressed PCM and have no samples at or above 0.999 amplitude. The installed API applies a 60 Hz high-pass, gentle compression and peak normalization. Neither the sample rate nor the absence of clipping diagnoses the reported grain. It may originate in the model, phonemization or processing; those are hypotheses, not listening conclusions.

The [release-specific Kitten guide](https://github.com/debpalash/VoiceStudio/blob/v0.5.6/docs/engines/kittentts.md) documents speed as its available delivery control. The [Supertonic guide](https://github.com/debpalash/VoiceStudio/blob/v0.5.6/docs/engines/supertonic3.md) describes another CPU preset engine with separate weights/terms; it is only a later comparison candidate, not proof of superior quality or permission to install it. Higher sample rate alone is not an acceptance criterion.

## Completed Bella refinement — separate approval

One neutral Bella take was synthesized with the installed CPU adapter at speed **1.15**. Both files below use that exact retained waveform. Each lasts **23.966667 seconds**, about **123 input words/minute including pauses**. This is shorter than the original 26.716667-second Bella sample; the control setting does not establish an exact proportional duration reduction.

[Raw / gain only](<C:/Youtube Automation Obsidian/voice_samples/voicestudio_trial_01/bella_refinement_01_raw.wav>) · [VoiceStudio processing](<C:/Youtube Automation Obsidian/voice_samples/voicestudio_trial_01/bella_refinement_01_mastered.wav>)

| Comparison | RMS | Peak | Duration |
|---|---|---|---|
| Raw, gain adjustment only | -20.0005 dBFS | -1.0064 dBFS | 23.966667 s |
| Same take, 60 Hz high-pass + 1.5:1 compressor, then gain | -20.0001 dBFS | -3.4858 dBFS | 23.966667 s |

Both are 24 kHz mono PCM 16-bit WAV with zero full-scale clipped samples. The native float waveform is retained for provenance; the comparison uses no denoiser, reverb, resampling or added saturation. RMS matching is not a claim of exact perceived-loudness matching. Model synthesis took 14.500 seconds; generation plus processing/accounting took 23.265 seconds. Sampled process RSS peaked at about 614.5 MiB. Trial allocation increased by about 6 MiB to about 5.473 GiB, within the 16 MiB additional and 10 GiB overall limits. No downloads, installs, paid service, cloud synthesis, cloning or episode narration occurred.

The first direct adapter entry stopped in language validation because the runner omitted the installed resources root from its import path. The preserved traceback/source order shows that it never reached `_synthesize` and produced no waveform. The import path and explicit language preflight were repaired without changing the installed app or approved proposal. The completed run then recorded exactly **one actual synthesis call**. Failure and repair receipts remain beside the completed manifest; no failed synthesis was automatically retried.

**Historical next action after generation:** compare the Bella copies. Brody subsequently rejected their slow/grainy texture; see the recorded outcome below.

## Refinement listening outcome — Kitten parked

Brody reports that the raw and processed versions sound effectively identical and remain slow/grainy. The tentative Bella preference is not production quality acceptance. This comparison suggests light mastering is not the main issue; it does not establish the exact source of the texture. Further EQ/denoising is not the next pilot task. This finding applies to this Kitten/Bella setup, not every model usable in VoiceStudio.

**Historical recommendation before the Mia request:** one neutral Mia comparison at speed 1.0, max 400 existing credits, no extra spending or retry. This was later authorized and completed; see the current result above. It did not consume or restart the held Amy request.

The completed Mia request preserved a 276-credit pre-call quote; specific signed-in history reported 61 credits used and 9,939 remaining. The post-call subscription connector was stale. See [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/elevenlabs_mia_neutral_provider_history_2026_10_20.json|provider-history evidence]]. No new software/model was installed or removed for Mia.
