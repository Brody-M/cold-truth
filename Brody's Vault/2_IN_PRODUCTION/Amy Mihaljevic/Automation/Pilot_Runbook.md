# Amy pilot — direct production runbook

**Current result, 2026-10-21:** **M6 reviews approved:** Brody approved the three Shorts script/outline pairs, exact proposed visual uses/rights conditions and full synchronization playback. Finals,142 captions and the approved asset registry now pass their binding checks. The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/Next_Production_Scope|next bounded production scope]] is prepared for three Shorts requests and four local review videos. New narration/rendering remains unauthorized; use the [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/M6_Preparation_Handoff|current handoff]]. Historical procedures below predate the completed reviews; the live handoff and exact receipts take precedence.

[[00_START_HERE|Home]] → [[0_ADMIN/PROJECT_DASHBOARD|Queue]] → [[2_IN_PRODUCTION/Amy Mihaljevic/Production_Summary|Amy status]] → Runbook

**Prepared 2026-10-20. M4 scope: offline implementation and procedure.** M3 is complete: Brody approved the full draft and reverse outline together with “they look good cont.” The original reviewed documents and review JSON remain unchanged. [[2_IN_PRODUCTION/Amy Mihaljevic/Script_Final|Approved final]] changes only title/status metadata; its narration equals the reviewed draft. The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/script_approval_2026_10_20.json|paired approval record]] binds the packet, draft, outline, final and extracted text.

**Historical readiness checkpoint, 2026-10-20:** earlier rate/hold checks below precede the separate current normal-speed scope and completed attempt.

Amy raw/processed audio now exists. Full listening QA, passing complete preflight, alignment, rights-cleared visuals, Shorts and masters remain incomplete. The configured automated production route stays disabled.

## M5 — one bounded narration attempt, after explicit Phase 2 approval

The original [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/narration_scope_proposal.json|narration scope proposal]] is retained unchanged. Its separate Phase 2 approval now grants this scope: one ElevenLabs Mia request, using the exact 7,835-character UTF-8 spoken-text input, at most **8,000 existing provider credits**, no overage, purchase or subscription change, no automatic retry or fallback. This is a proposed ceiling, not a price quote or evidence of available balance. Check the current voice, account access, input limit and charge multiplier before submission; stop if the request cannot be confirmed within the ceiling. A failed/uncertain response consumes the single attempt until its billing/result is reconciled. No second request is implicit.

| Setting | Exact proposed value |
|---|---|
| Tool | `mcp__elevenlabs__text_to_speech` (available tool schema inspected; not invoked) |
| Voice | `nPpkc230TdYdntJKFNby` — selected Mia profile |
| Model / language | `eleven_multilingual_v2` / `en` |
| Stability / similarity | `0.72` / `0.76` |
| Style / speed / speaker boost | `0.05` / `0.94` / `true` |
| Output | `mp3_44100_128` |
| Input | `Automation/Narration_Text.txt`, SHA-256 `00157d1ad4473c3dbd447073c71baf54053ff85e62344a1149e5d7a5640eed37` |
| Canonical audio | `Audio/Amy_Mihaljevic_Mia_attempt_01.mp3` inside this episode |
| Provider output directory | `Audio/provider_attempt_01` inside this episode; preserve its one returned file and record its actual path |

The tool schema accepts every locked setting. Its filename is provider-selected, so approve that single output directory plus a byte-identical copy to the canonical audio path. Record both exact paths and hashes after return. Never submit Markdown, headings, paragraph IDs, source links or B-roll cues to narration. Revalidate the paired approval immediately before submission. No narration has been sent during M4.

For a future separately authorized request, save a **new, uniquely named** approval record (never overwrite `Automation/approvals/phase_2_narration_approval.json`) with the real human decision/quote/date, exact approved proposal hash, script/text bindings, actions, settings, limits and paths. Do not edit the proposal into a historical approval. Include `human_approved: true`, `approved_by`, `approved_on` or `approved_at`, `user_quote`, `scope`, `case_id`, `target_format`, `script`, `narration_text`, `authorized_actions: ["narration"]`, `settings` and `output_paths`. The checker's file binding is always `{path, sha256, bytes}` with a workspace-relative path.

Record the attempt before calling and reconcile its result afterward. Preserve tool, UTC timestamp, request settings, input bindings, requested/actual outputs, attempt number, provider request identifier if supplied, estimated/actual credit use and failure details without secrets. Store an immutable attempt receipt at `Automation/narration_attempt_01.json`; append a reference to the existing direct-generation manifest. A receipt has `entries`, containing one event with `event_id`, `case_id`, `target_format`, `script`, `narration_text`, `phase_2_scope` (approval file binding), `tool`, `recorded_at_utc`, `settings`, `outputs` (all output bindings), and billing/result details. Binding an immutable receipt avoids invalidating preflight whenever the project-wide manifest gains another entry.

Listen to the **whole** exact audio against the approved text. Check omissions, extra words, pronunciation, calm delivery, peaks, clipped words, gaps and the ending. Save `Automation/audio_qa_01.json`, with named reviewer/decision fields, `script`, `audio` bindings, `full_listen_passed: true` only after actual listening, and any issues. An assistant must not fabricate human playback. Technical measurement does not verify the spoken story.

Build `Automation/audio_preflight_request.json` with:

```json
{
  "case_id": "amy-mihaljevic",
  "case_name": "Amy Mihaljevic",
  "target_format": "youtube-longform",
  "script_approval": {"path": "WORKSPACE_RELATIVE_APPROVAL", "sha256": "ACTUAL", "bytes": 1},
  "script": {"path": "WORKSPACE_RELATIVE_FINAL", "sha256": "ACTUAL", "bytes": 1},
  "narration_text": {"path": "WORKSPACE_RELATIVE_TEXT", "sha256": "ACTUAL", "bytes": 1},
  "audio": {"path": "WORKSPACE_RELATIVE_AUDIO", "sha256": "ACTUAL", "bytes": 1},
  "phase_2_scope": {"path": "WORKSPACE_RELATIVE_PHASE2_APPROVAL", "sha256": "ACTUAL", "bytes": 1},
  "generation_manifest": {"path": "WORKSPACE_RELATIVE_IMMUTABLE_ATTEMPT_RECEIPT", "sha256": "ACTUAL", "bytes": 1},
  "generation_event_id": "ACTUAL_EVENT_ID",
  "audio_qa": {"path": "WORKSPACE_RELATIVE_QA", "sha256": "ACTUAL", "bytes": 1}
}
```

The example is deliberately non-executable. Fill every binding from actual bytes with `pilot_evidence.describe`; do not use placeholders as evidence. Commands below run from the workspace root with the installed Python interpreter:

```powershell
python -B automation/pilot_evidence.py approval "Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/script_approval_2026_10_20.json"
python -B automation/pilot_evidence.py --output "Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Automation/preflight.json" audio "Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Automation/audio_preflight_request.json"
```

The audio check invokes FFprobe with a 30-second timeout, measures the selected **audio stream**, rejects missing/nonfinite/zero durations and never substitutes container duration. It compares Decimal durations before rounding. `<480.000` blocks long-form; `>60.000` blocks Shorts without their exact exception. It checks script/outline/supporting inputs, approval, source text, audio, Phase 2 scope, generation receipt and full-listen receipt, including a second binding check after probing. A runtime failure writes a blocked report and exits nonzero. Binding/probe failures exit blocked without creating a pass report. Outputs use exclusive creation; archive a prior report under a distinct path before rerunning, and always regenerate the canonical report against the current inputs before alignment/assembly.

`assembly_allowed` is the audio gate, **not independent permission to assemble**. M6 still needs its production scope, licensed assets and reviewed timing. A changed input makes prior reports stale. Never slow speech, insert silence or repeat narration to reach eight minutes. Return to editorial review for meaningful changes, or request a specific documented Short-Format exception. No exception is currently approved. Exception metadata retains the standard's `case`, `target_format`, `exception_type`, `human_approved`, `approved_by`, zoned `approved_at`, and `reason`, plus `case_id`, actual `user_quote`/`scope` and exact script/audio bindings. Short-Format also binds a Production Summary actually labeled `Short-Format`.

## M6 — timing, independent visuals and masters

M6 requires additional explicit Phase 2 scope. Do not interpret narration-only approval as visual-sourcing or rendering approval. The alignment route is manual transcript timing in the operator's editor, normalized into JSON and exported by the local checker to SRT; it does not depend on an uninstalled WhisperX adapter. Local FFmpeg 8.1.1 exposes its `subtitles` filter. M4 verified the JSON/SRT interface with inert fixtures and inspected FFmpeg/FFprobe version/help only. It did not align an episode, render a sample or install an editor/model.

For the exact approved audio, an operator listens and enters short caption segments (`start`, `end`, `text`), at most six seconds each. Match every spoken word in order. Review placement through the full track. Save `Automation/alignment.json` with exact `audio`, `script`, `narration_text` bindings, `tool`, `recorded_at_utc`, `segments`, and a `timing_review` containing the real human decision fields plus `full_listen_passed: true`. Word order, finite times, monotonic nonoverlap, bounds and text coverage are checked; perceptual sync, pronunciation and useful line wrapping require actual playback.

```powershell
python -B automation/pilot_evidence.py --output "Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Automation/alignment_check.json" alignment "Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Automation/alignment.json" "Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Automation/audio_preflight_request.json" --srt-output "Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Audio/Amy_Mihaljevic.srt"
```

This reruns the audio probe and bindings; it cannot reuse an unverified old pass. Save the actual editor/project settings and any SRT/assembly output in the direct manifest.

Maintain `Visuals/Longform` and `Visuals/Shorts` as distinct pools. Long-form uses downloaded Pexels B-roll and case graphics with factual captions. Shorts use independently licensed or recorded **Orbital gameplay** and factual overlays. Do not share visual assets, including graphics, screenshots, clips or transformed versions of the same source. License evidence is local saved terms/permission/recording evidence with source URL, creator, access/download date, use restrictions, attribution and review notes. Do not infer a case-photo license from its appearance on an official page.

Create `Automation/asset_registry.json` declaring `synthetic: false`, with nonempty `youtube-longform` and `shorts` arrays. Each entry contains `asset_id`, `source_identity` (stable provider/source ID; transformations preserve it), `asset_class` (`pexels_broll` or `case_graphic` for long-form; `orbital_gameplay` for Shorts), `file` binding, `license_evidence` binding, and `rights_review` binding. The named review JSON contains actual human decision fields, matching `asset`, `license_evidence`, `source_identity`, `permitted_track`, `commercial_use_reviewed: true` only after assessment, and `credits` (credit text or explicit documented reason no attribution is required). Preserve all URLs/rights rationale inside the evidence/review; the checker cannot decide legal validity or recognize renamed/transformed footage visually.

```powershell
python -B automation/pilot_evidence.py --output "Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Automation/asset_check.json" assets "Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Automation/asset_registry.json"
```

The check recomputes hashes, verifies nonempty files and bound rights evidence/review, rejects wrong classes and collisions in asset IDs, source identities, canonical paths, content hashes or physical files. Both pools must exist before overall visual readiness; a shot list or URL list is insufficient. It cannot prove the bytes are decoded media or prove visual/source identity if an operator falsely labels a transformed file. Check actual content in playback and preserve source identity honestly. Rerun immediately before assembly and after changes.

Prepare **3–5** standalone source-backed Shorts scripts from the approved final/ledger, with factual overlays and no theory invitation. Each needs its own reviewed script approval, narration scope/attempt/QA, `target_format: shorts`, measured audio, alignment and branch-local `Automation/preflight.json`. The checker supports the same paired-review record structure for each branch. Do not treat a cut long-form audio clip, reading estimate or long-form preflight as a Short's narration evidence.

Before assembly, verify the exact timeline uses approved narration, reviewed alignment and its track's approved pool only. All timeline asset IDs and source file bindings must be in the registry. Record the project/timeline, tool/version/settings, exact inputs and every output. Assembly is a manual operator step with these checks; there is no new automated renderer or orchestrator adapter. Keep long-form and Shorts projects/output paths separate.

After explicitly authorized rendering, run `ffprobe -v error -show_streams -show_format -of json PATH_TO_MASTER` and preserve its result with the master hash. Check a decodable video and audio stream, intended 1920×1080 long-form or 1080×1920 vertical framing, intended frame rate, intelligible level, no clipping, audio/video endpoint consistency, captions/overlays inside safe areas and source duration policy from the approved narration. Decode checks and an operator **full master playback** are required: verify chronology, pronunciation, sync, transitions, black/frozen frames, visual relevance, separation, overlay readability, ending and all credits. Record reviewer/date, defects/fixes and exact master binding. No machine metadata pass substitutes for that review. Resolve defects before M7.

## Release handoff and limits

M7 prepares exact reviewed masters, captions, sources/credits, rights evidence, honest metadata, approved thumbnail and actual channel/account readiness. Recheck the October 16 current-status/reward claims before release; changed narration returns to paired review. M8 requires exact publishing authority. M9 measures real effort, credits, rework and bottlenecks before promising cadence. There is no release date or scheduled background job.

The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/M4_Offline_Checks|M4 check record]] records what was actually verified. FFprobe and the file checker can now validate real artifacts after authorization; live provider behavior, correct media, sufficient runtime, rights validity and creative quality remain unproven until the real pilot.
