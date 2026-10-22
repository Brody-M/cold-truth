# Amy — quieter narration and pacing pilot03

[[2_IN_PRODUCTION/Amy Mihaljevic/Automation/M6_Preparation_Handoff|Current handoff]] · [[0_ADMIN/PROJECT_DASHBOARD|Queue]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/Media_Revision_02|Earlier pop repair and visual revision brief]]

**2026-10-21 feedback:** Brody reports improved sound after correction02, but excessive pauses make the story hard to follow and the track still needs to be quieter. This is a changes request, not a full-audio or master approval. [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/audio_feedback_correction02_2026_10_21.json|Exact feedback and reviewed-file bindings]].

The existing draft has58commas and89sentence segments. Machine timing shows a median0.581second gap after a comma and1.040seconds after a sentence;44 of58 comma gaps exceed half a second. Those word-boundary measurements identify candidates; they do not alone identify safe silence or establish natural pacing.

The Editor has produced an additional **−3dB full-length level reduction** and a matched-level opening pacing comparison. The full gain-only WAV retains25,161,728samples /570.560725624seconds and measures−40.14LUFS /−27.81dBTP. The pop repair from correction02 remains in place.

The opening pilot has **eleven verified quiet-interior cuts**, shortening56.700seconds to53.416871seconds. Each cut has at least80ms protection from aligned words, measured low RMS/peak energy and5ms fades in quiet shoulders. All actual cut boundaries, sum math and output hashes were checked. Both comparison clips have the same−3dB sample gain; there is no voice acceleration or changed script wording. Numerical tests cannot guarantee natural delivery or perfect breath/phoneme classification.

Before — same quieter level:

![Opening before pacing edit](<C:/Youtube Automation Obsidian/Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Audio/correction_03/pilot_first_two_paragraphs_before_minus3db.mp3>)

Pacing pilot — same quieter level:

![Opening pacing pilot](<C:/Youtube Automation Obsidian/Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Audio/correction_03/pilot_first_two_paragraphs_pacing_minus3db.mp3>)

[Full quieter9:31 audio — level change only](<C:/Youtube Automation Obsidian/Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Audio/correction_03/Amy_Mihaljevic_Mia_correction_03_gain_only.mp3>) · [[2_IN_PRODUCTION/Amy Mihaljevic/Audio/correction_03/Audio_Correction_03_Report|Editor report]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Audio/correction_03/audio_correction_03_receipt.json|Exact processing/cut receipt]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/audio_pacing_review_03.json|Exact listening-review bindings]].

**The full episode has not received a pacing edit.** The strict quietness screen found only these eleven cuts;125 later punctuation gaps failed its quiet-run criteria. Those sections need closer waveform-guided editing and listening, because stronger activity must not be blindly classified as disposable silence. The screened3.283129second reduction would leave567.277596seconds; this is a bound for this conservative plan, not the maximum feasible edit. All audio acceptance remains pending.

Editing silence can improve flow, but cannot fully change the recorded intonation or repair the delivery of a spoken phrase. If the pilot still feels unnatural, stop extending that technique and prepare a revised narration-performance approach for review; there are no provider attempts remaining under the existing grant.

Any later full pacing edit needs actual duration verification, new exact-audio QA/preflight and remapped/reviewed synchronization before video assembly. The existing142-caption alignment refers to the old timing. Do not apply it unchanged to shortened audio. The480.000second long-form floor stays in force; never add padding or slow speech to recover it.

**No video render consumed.** The one remaining long-form correction should combine accepted audio, improved relevant B-roll and the caption layout repair. Shorts audio/timing and publishing remain separate.

Method reference: [Descript’s official word-gap editing guide](https://help.descript.com/script-editing/shorten-word-gaps) describes selecting gap lengths and previewing surrounding audio. This local pilot uses existing installed tools; Descript was not installed or invoked. The proposed targets are editorial choices to audition, not a universal pacing standard.
