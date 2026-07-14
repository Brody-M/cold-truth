---
voice_id: nPpkc230TdYdntJKFNby
voice_name: Mia - Clear & Emotive Female Narrator
selection_status: selected
selection_date: 2026-07-09
selection_reason: Most natural and human-sounding delivery; use controlled settings to reduce occasional vocal peaks.
model_id: eleven_multilingual_v2
stability: 0.72
similarity_boost: 0.76
style: 0.05
speed: 0.94
use_speaker_boost: true
output_format: mp3_44100_128
config_variable: ELEVENLABS_VOICE_ID
---

# NARRATION_VOICE

## Current default

`nPpkc230TdYdntJKFNby` (Mia - Clear & Emotive Female Narrator) is Cold Truth's primary narration voice. All future narration calls must use this ID by default, unless `ELEVENLABS_VOICE_ID` is intentionally set to override it.

## Selection notes

Mia was selected after a direct comparison of three true-crime narration samples. Her delivery is the most natural, human-sounding fit for Cold Truth. Use measured pacing and moderate expressiveness to keep occasional loud peaks controlled; apply light compression, de-essing, and limiting during production when appropriate.

## Locked production preset

All future Cold Truth narration must use `eleven_multilingual_v2` with stability `0.72`, similarity boost `0.76`, style `0.05`, speed `0.94`, speaker boost enabled, and `mp3_44100_128` output. A deviation requires an episode-level note and an Automation manifest entry.

## Selection criteria

- Calm, close-mic documentary delivery with enough warmth for women 25-45, especially background listeners and mothers.
- Controlled tension and clear pacing for unresolved cases; never sensational or trailer-like.
- Strong intelligibility at normal and short-form playback speeds.

## Change procedure

1. Keep `voice_id` set to Mia's ID unless the channel owner intentionally selects a replacement.
2. Pass this ID to every narration request by default.
3. If overriding via `ELEVENLABS_VOICE_ID`, document the exception in the episode notes.
4. Production narration still requires explicit Phase 2 approval.
