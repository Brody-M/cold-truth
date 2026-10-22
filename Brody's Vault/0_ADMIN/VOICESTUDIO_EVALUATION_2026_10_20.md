# VoiceStudio — local narration evaluation

[[00_START_HERE|Home]] · [[0_ADMIN/PROJECT_DASHBOARD|Queue]] · [[0_ADMIN/GITHUB_TRENDING_REVIEW_2026_10_20|Tool comparison]] · [[0_ADMIN/PROJECT_MEMORY|Project memory]]

**Current execution result:** Brody approved the full **9:30.56** processed Mia narration on October21; the [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/preflight.json|audio preflight]] passes. One full request used **1,722 existing credits**; no attempts remain. The separately [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/phase_2_m6_preparation_2026_10_21.json|approved M6 preparation scope]] has produced exact-audio timing, local stock, original cards and verified existing Orbital provenance. The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/M6_Preparation_Handoff|M6 review hub]] records the completed script/rights/timing reviews and next execution scope. Video assembly/rendering, new narration and publishing are outside this grant. Kitten/Bella stays parked. The assessment below preserves pre-install findings; see [[0_ADMIN/VOICESTUDIO_CPU_TRIAL_2026_10_20|trial history]].

**Historical pre-install assessment — 2026-10-20:** evaluate VoiceStudio as a local narration front end. The later executed trials and current decision are recorded above; statements below about not-yet-run work describe that earlier checkpoint.

## What is established

[VoiceStudio](https://github.com/debpalash/VoiceStudio) documents local speech engines and HTTP/MCP integration. Its [MCP guide](https://github.com/debpalash/VoiceStudio/blob/main/docs/mcp.md) exposes health, voice listing, synthesis and transcription, plus file output confined to a configured directory. That is a useful integration route for the pilot; it is not tested on this PC yet. A GUI/API does not itself determine model quality or rights.

Read-only Windows checks found **AMD Ryzen 7 5800X**, **AMD Radeon RX 7900 XTX**, approximately **31.9 GiB physical RAM**, approximately **12.7 GiB available RAM at inspection**, and approximately **122.3 GiB free on C:**. Values are a snapshot. uv, Bun, Node and Git are present. CIM inventory was unavailable; the CPU/display names came from the Windows registry and memory from `GlobalMemoryStatusEx`. No NVIDIA driver command was found; this does not measure actual GPU compute or VRAM availability.

The [Windows guide](https://github.com/debpalash/VoiceStudio/blob/main/docs/install/windows.md) says the packaged PyTorch route accelerates NVIDIA on Windows; Radeon PyTorch engines use CPU. It describes a separate Vulkan path for audio.cpp, so the Radeon is not universally unusable. Do not install unsupported ROCm wheels or change the OS to force acceleration for this first trial.

The release page resolved to [v0.5.6](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6), an Electron release with a Windows installer link. Current `main` is ahead of that release: verify capabilities against the installed version and its OpenAPI/engine catalog. The release warns about unsigned installers. At the assessment checkpoint, no executable or checksum had been downloaded or verified; the completed-trial note above supersedes that installation status. The public GitHub API was inaccessible through web retrieval; shell DNS lookup also failed. Do not convert those failed metadata lookups into an installation-success claim.

An additional local check found no matching app in the readable machine uninstall registry and no response from the documented loopback `/health` endpoint. The user uninstall registry was unavailable, so this is not proof that no installation exists. Reuse any installation found in the actual setup pass.

## Engine choices for this PC

| Candidate | Evidence and limits | Pilot decision |
|---|---|---|
| Default OmniVoice | The application's [license notice](https://github.com/debpalash/VoiceStudio/blob/main/LICENSE-NOTICE.md) identifies the default pretrained weights as CC-BY-NC and distinguishes app, weight and tokenizer terms. | Do not choose the default for a commercial channel merely because the app is open source. |
| KittenTTS mini 0.8 | The [release-specific engine guide](https://github.com/debpalash/VoiceStudio/blob/v0.5.6/docs/engines/kittentts.md) documents an approximately 80 MB CPU model, preset voices and 24 kHz mono output. The [model card](https://huggingface.co/KittenML/kitten-tts-mini-0.8) labels it Apache-2.0. The [configuration](https://huggingface.co/KittenML/kitten-tts-mini-0.8/blob/main/config.json) maps Bella/Luna/Rosie/Kiki to the four female preset IDs. | First lightweight trial candidate. Start with Bella and Luna at normal speed. Confirm the actual engine/voice rather than accepting its documented silent fallback. Preserve model/component notices; audio quality and complete rights assessment remain unverified. |
| Supertonic-3 | Its [guide](https://github.com/debpalash/VoiceStudio/blob/main/docs/engines/supertonic3.md) describes CPU inference, 44.1 kHz output, approximately 400 MB weights and OpenRAIL-M terms requiring review/acceptance. | Second candidate if Kitten's delivery is unsuitable. No blanket commercial clearance or license acceptance recorded. |
| audio.cpp / Breeze-TTS-2 | The [engine catalog](https://github.com/debpalash/VoiceStudio/blob/main/docs/engines/README.md) documents Vulkan-capable execution but labels those weights research/noncommercial. | Not the commercial narration route simply to use the Radeon. |
| New KittenTTS 2 | The [upstream library](https://github.com/KittenML/KittenTTS) now distinguishes a newer speech model from its legacy ONNX models. | Do not assume VoiceStudio's mini-0.8 adapter supports it. Keep the initial trial pinned; an unbounded latest-package upgrade is not a compatibility test. |

These are selection findings, not a legal opinion or an independent voice-quality benchmark. The application license alone does not approve every component or a cloned speaker. Do not clone Mia from an ElevenLabs preview or output; provider migration is not speaker consent.

## Concrete next pass

The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/voicestudio_trial_proposal.json|trial proposal]] defines an isolated Windows CPU evaluation: stable Electron app, only Kitten mini 0.8, two neutral test clips, no case narration, no cloud provider, no paid service and a 10 GiB total disk-increase ceiling. Approximately 80 MB is the model alone; the app/runtime/dependencies are larger and must be checked against the ceiling. The proposal is not a record of an executed trial or a new Phase 2 grant.

1. Verify the official release asset and its published checksum. Use a user-selected workspace-contained trial data/cache/output area; leave global provider settings and existing media intact. Do not bypass a browser/OS trust warning or accept a new agreement on the user's behalf.
2. Install the CPU runtime and one pinned model only within the agreed bounds. Verify real health/catalog results, local-only binding, model revision, active engine, exact female preset and file output. Decline cloud/analytics setup; never assume a default is the intended engine.
3. Generate the two neutral samples only under the applicable trial scope, recording tools, settings, timestamps, every path, model/license evidence and durations. Measure real wall time and resource use; do not promise realtime performance from upstream claims.
4. Brody listens for calmness, intelligibility, name/date pronunciation and consistency. Only after selecting a replacement should the production profile and exact episode narration scope be updated. The one-attempt Mia approval does not transfer to this route.
5. Preserve the approved Amy wording. Run a representative longer continuity check before the full episode, then actual-audio preflight and whole-track QA. All 480-second/no-padding rules remain in force. VoiceStudio transcription/word timestamps may be evaluated later for M6; do not assume they equal a verified forced alignment.

**Current result:** the [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/voicestudio_bella_refinement_manifest.json|completed one-take refinement]] follows Brody's tentative Bella preference and slow/grainy feedback. Raw and normally processed copies of one faster neutral take await listening. No replacement production voice or episode scope is approved.
