# Mia sample — Editor audio pass

[[00_START_HERE|Home]] · [[0_ADMIN/PROJECT_DASHBOARD|Queue]] · [[0_ADMIN/ROLE_EDITOR|Editor job]] · [[0_ADMIN/VOICESTUDIO_CPU_TRIAL_2026_10_20|Comparison history]] · [[2_CHANNEL_SYSTEM/NARRATION_VOICE|Voice profile]]

**Historical comparison steps below; current result:** Brody accepted the latest peak-controlled sample with “its good enough proceed.” See [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/mia_sample_listening_acceptance_2026_10_20.json|bound listening acceptance]]. Full Amy narration is generated and processed; [[2_IN_PRODUCTION/Amy Mihaljevic/Production_Summary|episode listening review]] is next.

**Comparison context:** the neutral Mia sample is complete. Brody finds it “pretty good” but reports loud P sounds/peaks and requested an Editor agent to process the existing audio for later use with video. Brody subsequently requested that the whole clip be toned down. After that gain-only copy still felt too peaky, Brody requested a standard filter and professional-practice research. The current copy has stronger peak compression and lookahead limiting; listening review is pending. This is a neutral 49-word comparison, not Amy narration.

## Source and authority

The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/elevenlabs_mia_neutral_comparison_approval_2026_10_20.json|one-request approval]] and [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/elevenlabs_mia_neutral_attempt_01.json|completed request]] bind Mia / multilingual v2 / speed 1.0. Actual audio is 20.572880 seconds. One synthesis was made; zero attempts remain. The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/elevenlabs_mia_neutral_provider_history_2026_10_20.json|specific provider history]] confirms **61 credits used** and 9,939 remaining, within the 400-credit cap. The pre-call quote was 276; the subscription connector remained stale after generation.

The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/mia_neutral_audio_edit_authorization_2026_10_20.json|audio-edit direction]] authorizes an Editor agent to filter the existing sample offline. It does not authorize another synthesis or establish acceptance of the processed result. The original remains unchanged.

[Original Mia MP3](<C:/Youtube Automation Obsidian/voice_samples/elevenlabs_mia_trial_01/mia_normal_01.mp3>)

## Current peak-controlled copy

[Listen to peak-controlled MP3](<C:/Youtube Automation Obsidian/voice_samples/elevenlabs_mia_trial_01/mia_normal_01_peak_control.mp3>) · [Peak-controlled WAV](<C:/Youtube Automation Obsidian/voice_samples/elevenlabs_mia_trial_01/mia_normal_01_peak_control.wav>) · [Exact processing receipt](<C:/Youtube Automation Obsidian/voice_samples/elevenlabs_mia_trial_01/mia_normal_01_peak_control_receipt.json>)

Brody reported that peaks remained very loud and requested research into a popular filter and professional practice. [iZotope’s plosive guidance](https://www.izotope.com/community/blog/removing-plosives-from-a-voice-recording) distinguishes low-frequency P-pop repair from broad EQ. [Audacity’s dynamics guidance](https://support.audacityteam.org/audio-editing/reducing-dynamic-range-compressor-limiter) describes compression and limiting for level differences and peaks. Targeted repair or local gain edits followed by audition remain appropriate when individual consonants remain objectionable; a global measurement cannot label those sounds.

This revision uses the installed FFmpeg compressor and lookahead limiter, not an RX or Audacity plugin. [FFmpeg’s implementation documentation](https://ffmpeg.org/ffmpeg-filters.html#alimiter) supports disabling automatic leveling and compensating lookahead latency. Applied to the retained quieter WAV: peak compression at −22 dBFS, ratio 4:1, 1 ms attack, 100 ms release, no makeup gain; 4× oversampled limiting at −18 dBFS with 5 ms lookahead and 100 ms release; no automatic level boost; final −2 dB output gain. Existing low-frequency treatment is retained. No new treble cutoff, denoising, speech generation or installation occurred.

| Measurement | Previous quieter WAV | Current WAV | Current MP3 |
|---|---|---|---|
| Integrated loudness | −24.43 LUFS | −31.48 LUFS | −31.75 LUFS |
| True peak | −8.85 dBTP | −19.99 dBTP | −20.23 dBTP |
| Peak-to-RMS difference | 15.41 dB | 11.16 dB | 11.18 dB |

The master’s maximum true peak is **11.14 dB lower** than the previous quieter copy; its peak-to-RMS difference is reduced by 4.25 dB, so this is dynamic control as well as lower overall volume. The limiter actually engaged, reducing its input’s highest peak by 3.25 dB. Overall loudness is 7.05 LU lower. This is deliberately a quiet listening revision, **not a locked professional delivery loudness target**. All 907,264 decoded samples / 20.572880 seconds remain; no full-scale clipping. Technical checks alone cannot establish whether Brody’s specific consonant complaint is resolved. Brody subsequently accepted this exact revision with “its good enough proceed”; its master/preview hashes are recorded in the listening acceptance. The separate full episode still needs its own full listen.

## Earlier gain-only quieter copy

[Listen to quieter MP3](<C:/Youtube Automation Obsidian/voice_samples/elevenlabs_mia_trial_01/mia_normal_01_editor_quieter.mp3>) · [Quieter WAV](<C:/Youtube Automation Obsidian/voice_samples/elevenlabs_mia_trial_01/mia_normal_01_editor_quieter.wav>) · [Gain-adjustment receipt](<C:/Youtube Automation Obsidian/voice_samples/elevenlabs_mia_trial_01/mia_normal_01_editor_quieter_receipt.json>)

Brody’s direction: “the whole audio clip also needs to be toned down.” Applied constant **−4 dB gain** to the entire previously edited WAV, with no normalization or additional filtering. The current master measures **−24.43 LUFS / −8.85 dBTP**; the listening MP3 measures −24.70 LUFS / −9.12 dBTP. All 907,264 samples and 20.572880 seconds are retained. Constant-gain verification passes; no clipping, new speech, synthesis or credits. The original and earlier edited copies are retained. This is a sample-specific listening adjustment, not a newly locked production loudness target.

## Earlier Editor result

[Listen to edited MP3](<C:/Youtube Automation Obsidian/voice_samples/elevenlabs_mia_trial_01/mia_normal_01_editor.mp3>) · [PCM24 WAV for later editing](<C:/Youtube Automation Obsidian/voice_samples/elevenlabs_mia_trial_01/mia_normal_01_editor.wav>) · [Exact processing receipt](<C:/Youtube Automation Obsidian/voice_samples/elevenlabs_mia_trial_01/mia_normal_01_editor_receipt.json>)

The delegated Editor used an 80 Hz two-pole high-pass, gentle peak-detected 2:1 compression (−12.04 dBFS threshold, 2 ms attack, 100 ms release, no makeup gain), 0.5 dB attenuation, and a latency-compensated oversampled limiter at −2 dBFS. There was no blanket treble cut: numerical inspection found substantial low-frequency energy, while the source was not digitally clipped. This is a conservative trial treatment, not a diagnosis of particular consonants.

| Measurement | Original MP3 | Edited WAV | Listening MP3 |
|---|---|---|---|
| Integrated loudness | −17.77 LUFS | −20.43 LUFS | −20.70 LUFS |
| True peak | −0.76 dBTP | −4.85 dBTP | −5.11 dBTP |
| Decoded sample count | 907,264 | 907,264 | 907,264 |
| Decoded duration | 20.572880 s | 20.572880 s | 20.572880 s |

The edited WAV is 44.1 kHz mono PCM24. It preserves the exact decoded timeline: no cuts, time stretching, padding or new speech. PCM24 preserves this editing intermediate; it does not restore detail lost in the original MP3. The master is **2.66 LU quieter**, so compare at comfortable matched playback levels rather than judging by volume alone. Neither file has full-scale clipped samples.

The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/mia_neutral_audio_edit_validation_2026_10_20.json|technical verification]] checks file hashes, unchanged original, equal samples and the still-valid Amy script approval binding. No synthesis or provider credits were used for this edit. The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/direct_generation_manifest.json|direct manifest]] records the tool, settings and outputs. **Historical Editor checkpoint:** technical QA passed; later peak-control revisions and final sample acceptance are recorded above.

## Handoff to the eventual video

Use the lossless edited file only after listening acceptance. The present file is an internal voice test, so it cannot become the Amy soundtrack or pass the 480.000-second episode preflight. The actual episode now has a separately bound current scope, retained raw file, accepted processing and measured duration. Full episode listening still needs approval; then bind the passing preflight and later alignment to the exact approved hash. Do not time-stretch or pad narration. This pass assembles no video.

The earlier full-episode Mia grant is preserved unchanged; current direction resumed narration under a separate normal-speed scope. One full take now exists and all episode request attempts are used. Kitten/Bella remains parked. Follow [[0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2|M5 before M6]]; final visuals, rendering and publishing retain their applicable scopes.
