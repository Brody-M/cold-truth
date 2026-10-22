# Amy — professional audio reassessment04

[[2_IN_PRODUCTION/Amy Mihaljevic/Automation/M6_Preparation_Handoff|Current handoff]] · [[0_ADMIN/PROJECT_DASHBOARD|Queue]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/Audio_Pacing_Revision_03|Earlier pacing test]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/Media_Revision_02|Retained visual revision brief]]

**2026-10-21: correction03 is not accepted.** Brody reports persistent breathiness and perceived peaks and requests a professional approach. [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/audio_feedback_revision03_2026_10_21.json|Exact feedback/bindings]]. Earlier partial improvement and technical meters do not pass audio QA.

## What professional guidance changes

A pop filter or windscreen prevents microphone air blasts at recording; existing audio needs localized de-plosive/spectral treatment. A general low cut can thin the voice and leave distortion. [iZotope’s plosive repair guidance](https://www.izotope.com/community/blog/removing-plosives-from-a-voice-recording).

Between-phrase breath events need separate detection and gain reduction. Voiced speech and breath noise should be distinguished by harmonic content, with removed audio checked for damage. [iZotope Breath Control documentation](https://downloads.izotope.com/docs/rx6/18-breath-control/index.html).

Sharp S/SH sounds need frequency-selective de-essing, with frequency, threshold and maximum reduction chosen for the recording. This is distinct from a low-frequency P/B repair. [Apple’s de-essing guidance](https://support.apple.com/en-us/102006).

Those sources explain techniques; RX and Logic were not installed or used. [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/professional_audio_reassessment_04.json|Research record and explicit local inferences]]. The current audio is synthesized; do not infer a physical microphone failure. Breathiness throughout words and unsuitable inflection may be features of the selected take that local repair cannot transparently remove.

## Local diagnostic scope

**The focused13.2-second audition is ready.** A smooth gain dip starts2.160seconds, reaches−8dB at2.175, holds through2.260 and recovers to unchanged gain at2.320. The human-marked2.180–2.250 region measures−8.00dB in RMS and peak. The following2.350–2.600 syllable is unchanged. The consonant is attenuated, never removed or gated.

A single standalone gap-noise event at6.050–6.285seconds receives a modest−6dB dip with ramps. No EQ, de-esser, new limiter, normalization, additional overall gain or timing change is applied. The marked event is dominated by low/low-mid energy; a high-frequency de-esser is not justified for it. Both previews decode to582,120samples /13.2seconds. An independent saved-PCM check confirms exact identity outside the two treatment windows; preserved-word intelligibility and listening comfort still need an actual audition.

Before — unchanged correction03 baseline level:

![Marked onset before](<C:/Youtube Automation Obsidian/Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Audio/diagnostic_04/opening_13p2s_before.mp3>)

Targeted onset repair — same overall gain/timing:

![Marked onset repair](<C:/Youtube Automation Obsidian/Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Audio/diagnostic_04/opening_13p2s_onset_repair.mp3>)

[[2_IN_PRODUCTION/Amy Mihaljevic/Audio/diagnostic_04/Diagnostic_04_Report|Editor report and limitations]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Audio/diagnostic_04/diagnostic_04_receipt.json|Exact commands/settings/measurements]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/audio_diagnostic_review_04.json|Review bindings]]. A removed-only audio diagnostic is retained alongside these files; it intentionally includes the attenuated consonant and is not a clean breath/noise separation.

This is a local test, not a repaired full master. No TTS, installations, downloads or video render occurred. The existing full narration, captions and visual timeline are untouched.

**Precise human locator received:** the onset of “disappeared,” about2seconds into the opening, is the main reported spike. Existing machine timing places the word at2.181–2.801seconds. Brody clarifies breathiness is between phrases and is not severe. Prioritize smooth local onset-gain reduction and inspect that marked event; keep breath reduction modest. [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/audio_fault_disappeared_2026_10_21.json|Exact locator and quote]]. Broad extra filtering is not justified merely by an overall breathy impression. Perceptual success requires listening; signal metrics do not establish a professional-sounding result. Master QA and assembly remain blocked. The one corrective long-form video render remains available; actual Short audio/timing reviews and publishing remain separate.

For the marked word, the relevant professional step is local gain adjustment: [iZotope’s vocal-editing guide](https://www.izotope.com/community/blog/vocal-editing-101) describes lowering distracting words or phrases while preserving dynamics. The exact gain/ramp remains an audition choice for this recording.
