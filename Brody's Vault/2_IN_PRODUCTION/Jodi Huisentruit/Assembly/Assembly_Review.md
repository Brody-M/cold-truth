# Jodi Huisentruit - Assembly Review

**Status:** The v4 FCPXML and local master are technically valid but creatively rejected and audit-only. `Script_Final_v2.md` is no longer approved as the narrative foundation, and no active long-form release master exists. The v4 master is not approved for upload, scheduling, publishing, or release. All long-form scripts, audio, alignments, timelines, previews, renders, sources, and manifests remain preserved for auditability. The separately scripted Shorts track remains technically separate and unchanged; no Shorts publication is authorized. Nothing was uploaded or published.

## Checkpoint 13 historical assembly

- **Project:** `Jodi_Huisentruit_Longform_Preview_v4.fcpxml` — 1920 x 1080, 30 fps, 325.079 seconds.
- **Content:** 54 contiguous beats: 53 moving beats using 53 distinct valid Pexels resources from the approved v3 pool, plus one intentional “There is no resolution to offer” case card.
- **Validation:** no unmatched beats, no source-duration overruns, no timing gaps or overlaps, and no long-form/Shorts asset sharing.
- **Shorts decision:** `Shorts_Package.md` is a separately authored script with its own 37.877-second Mia narration and nine-marker WhisperX map. The long-form redundancy edit did not alter it, so no Shorts narration or preview regeneration was needed.
- **Render authorization:** Checkpoint 13 was approved; only the v4 long-form master was rendered. Shorts were not touched or rendered.

## Narrative rewrite status

- **Failure analysis:** `../Editorial/Narrative_Failure_Analysis.md` documents the structural rejection of `Script_Final_v2.md`.
- **Reverse outline:** `../Editorial/Story_Outline_v3.md` is source-bound to JH-01 through JH-07 and fully excludes JH-PI-01.
- **Current script:** `../Script_Draft_v3.md` is a 714-spoken-word from-zero draft. It is not a final script and is not approved for narration.
- **QA:** `../Editorial/Narrative_QA_v3.md` passes draft-level coherence and source checks but does not replace the paired human Narrative Coherence Gate.
- **Production stop:** no narration, WhisperX alignment, visual sourcing, Shorts derivation, FCPXML rebuild, render, upload, scheduling, or publishing may begin until the reverse outline and a future final script are explicitly approved together.

## Long-form v4 render verification

- **Master:** `../Renders/Jodi_Huisentruit_Longform_v4_1920x1080.mp4`
- **Size:** 225,738,589 bytes.
- **Picture:** H.264, 1920 x 1080, 30 fps, 9,753 frames, 325.100 seconds.
- **Audio:** mono AAC, 44.1 kHz, 325.079002 seconds.
- **Preview match:** the approved FCPXML/narration endpoint is 325.079365 seconds. AAC differs by 0.000363 seconds, within packet precision. At 30 fps, the enclosing complete picture-frame boundary is 325.100 seconds, 0.020635 seconds after the sequence endpoint and less than one frame. The approved narration, visual order, cuts, and timing were not altered.
- **Creative disposition:** technically valid, creatively rejected, audit-only, and prohibited from upload, scheduling, publishing, or release.
- **Supersession:** long-form masters v1-v3 remain fully superseded and audit-only. v4 is also audit-only; there is currently no active long-form release master.
- **Publishing status:** local render only; no upload, scheduling, publishing, or platform connection occurred.

## Checkpoint 12 redundancy edit

- **Script:** `../Script_Final_v2.md` — 719 narration words, down from 754.
- **Narration:** `../tts_At_ro_20260710_213842.mp3` — Mia locked preset, 325.079 seconds, one generation.
- **Alignment:** `WhisperX/tts_At_ro_20260710_213842.json` — local WhisperX word alignment.
- **Retimed plan:** `../YouTube_Visual_Timeline_v4.md` — 54 beats averaging 6.02 seconds.
- **Hard stop:** no FCPXML rebuild and no render before Checkpoint 12 approval.

## Superseded historical long-form preview

- **Project file:** `Jodi_Huisentruit_Longform_Preview.fcpxml`
- **Sequence:** 1920 x 1080, 30 fps, 16:9
- **Narration source:** `tts_At_ro_20260709_192446.mp3`
- **Verified narration runtime:** 5:26.766
- **Visual order:** all 14 approved Pexels shots, in numbered shot-list order.
- **Audio/visual alignment:** each shot starts at its scaled shot-list cue. The original shot plan estimated 5:55; visual timing was adjusted to end exactly with the verified narration.
- **Clip-duration treatment:** seven still/slow-motion-safe clips use editable speed holds. Shot 6 and Shot 11 play at normal speed, then move to editable static case-card placeholders so visible people and hand movement are not artificially slowed.

## Shorts preview

- **Project file:** `Jodi_Huisentruit_Shorts_Preview.fcpxml`
- **Sequence:** 810 x 1440, 30 fps, 9:16 crop from the licensed 2560 x 1440 gameplay source.
- **Narration source:** `tts_Befor_20260709_192610.mp3` (regenerated from the approved package)
- **Verified narration runtime:** 0:37.877
- **Gameplay source:** the separately licensed Orbital Minecraft parkour file in `../shorts_gameplay/`.
- **Overlay mapping:** all 9 markers are WhisperX-aligned to exact local word timestamps. The alignment JSON is stored at `WhisperX/tts_Befor_20260709_192610.json`; the rebuilt FCPXML contains the same marker times.
- **Credit placement:** `Gameplay footage by Orbital - No Copyright Gameplay` is present in `../Shorts_Metadata.md`.

## Review flags

1. The long-form audio is 28.234 seconds shorter than the original 5:55 visual estimate. Seven slow holds remain, all on non-human/vehicle motion. Two static case-card placeholders require final editorial design before render.
2. **Shorts alignment complete:** local WhisperX alignment verified all nine overlay anchors against the regenerated 0:37.877 audio. The `7:13 A.M.` and `Last known contact: June 27, 1995` labels are visual-only package facts and are anchored to the starts of their corresponding spoken sentences. No marker remains script-estimated.
3. The licensed Shorts gameplay is landscape 2560 x 1440, not native vertical. The preview applies a centered 9:16 crop at 810 x 1440; check composition in the editor before rendering.
4. No long-form Pexels file appears in the Shorts project, and no Shorts gameplay file appears in the long-form project.

## Render verification

| Master | Export | Preview match verification |
|---|---|---|
| Long-form | `../Renders/Jodi_Huisentruit_Longform_1920x1080.mp4` — 1920 x 1080, 30 fps, 189,105,106 bytes | The 326.766-second FCPXML sequence is represented by 9,803 frames (326.7667 seconds); AAC narration is 326.7660 seconds. The 0.0007-second difference is sub-frame/AAC packet rounding. |
| Shorts | `../Renders/Jodi_Huisentruit_Shorts_810x1440.mp4` — 810 x 1440, 30 fps, 39,832,533 bytes | The FCPXML’s 37.8774375-second audio and all nine aligned marker timings are preserved. AAC narration measures 37.8770 seconds; the 30 fps picture reaches 37.900 seconds, its nearest complete-frame boundary (0.0226 seconds). |

- Exports use only the assets specified in their respective FCPXML previews; the two visual tracks remain separate.
- The final end-frame holds and any end silence are timing normalization only. They do not alter narration, clip order, cue points, or overlay-marker alignment.
- No upload or publish action occurred.

## Long-form v2 — Checkpoint 9 preview

- **Project file:** `Jodi_Huisentruit_Longform_Preview_v2.fcpxml`
- **Alignment source:** local WhisperX word alignment, `WhisperX/tts_At_ro_20260709_192446.json`; no ElevenLabs call or new narration generation was used.
- **Sequence:** 1920 x 1080, 30 fps, 326.766 seconds; 57 contiguous visual beats (56 existing Pexels clip instances plus one static case-card placeholder), averaging 5.73 seconds.
- **Sync correction:** Shot 1 now begins at 0:00 with the existing analog-clock footage, matching “At roughly 4:10 in the morning, a colleague called Jodi.” The wet-pavement asset is first used at 0:17.275, precisely with “Public reporting described drag marks…”
- **Pacing correction:** all 14 approved long-form assets are reused as short cutaways. No new footage was sourced because each spoken beat has a safe existing visual match; the only graphic placeholder is the exact “There is no resolution to offer” card at 4:16.044–4:18.825. The following anniversary lead-in is a separate clock cutaway.
- **Validation:** XML parsed successfully; 57 visual beats cover 0:00.000–5:26.766 without gaps or overlaps; all 14 original Pexels asset references are used; no Shorts asset is present. All under-10-second repeat risks found in review were replaced with existing alternate clips; the final repeat audit has no returns within 10 seconds.
- **Render status:** rendered locally as `../Renders/Jodi_Huisentruit_Longform_v2_1920x1080.mp4`. The v1 long-form master must not be used for final review, upload, or publishing.

## Long-form v2 render verification

- **Master:** `../Renders/Jodi_Huisentruit_Longform_v2_1920x1080.mp4`
- **Size:** 198,465,439 bytes.
- **Picture:** 1920 x 1080, 30 fps, 9,803 frames.
- **Runtime:** video 326.7667 seconds; AAC narration 326.7660 seconds. This matches the 326.766-second FCPXML v2 sequence at the nearest 30 fps frame and AAC packet boundaries.
- **Publishing status:** local render only; no upload or publish action occurred.

## Long-form v3 — expanded Pexels sourcing / Checkpoint 11

- **Project file:** `Jodi_Huisentruit_Longform_Preview_v3.fcpxml`
- **Sourcing record:** `Pexels_Sourcing_v3.json` and `YouTube_Visual_Timeline_v3.md`; every moving beat records three Pexels search phrases and its exact WhisperX-spoken line.
- **Selected library:** 56 moving clips use 53 distinct Pexels video IDs. The broadened second pass added eight visually approved new clips. Three genuine thematic reuses resolve remaining beats: beat 23 reuses dispatch beat 14, beat 30 reuses official-contact beat 54, and beat 51 reuses quiet-current-status beat 46. No selected clip returns within 10 seconds.
- **Case card:** beat 44 remains the sole intentional static card: “There is no resolution to offer.” All other prior gaps are resolved.
- **Visual QC:** both first- and second-pass contact sheets were reviewed. Unsafe or unrelated candidates were excluded rather than silently substituted.
- **Validation:** v3 XML parsed successfully; 57 visual beats cover 0:00.000–5:26.766 with no timing gaps or overlaps. No Shorts gameplay is referenced.
- **Render status:** rendered locally as `../Renders/Jodi_Huisentruit_Longform_v3_1920x1080.mp4`. Do not use v2 for final review, upload, or publishing.

## Long-form v3 render verification

- **Master:** `../Renders/Jodi_Huisentruit_Longform_v3_1920x1080.mp4`
- **Size:** 214,557,340 bytes.
- **Picture:** 1920 x 1080, 30 fps, 9,803 frames.
- **Runtime:** video 326.766016 seconds; AAC narration 326.766009 seconds. This matches the 326.766-second v3 FCPXML sequence at frame/AAC packet precision.
- **Publishing status:** local render only; no upload or publish action occurred.
