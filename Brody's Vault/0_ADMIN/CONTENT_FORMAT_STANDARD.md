# Cold Truth Content Format Standard

**Status:** Locked standing rule  
**Applies to:** Strategist, Writer, Editor, Voice, Shorts Editor, Visual Producer, Assembly, and Upload Manager stages  
**Canonical audience:** women 25–45, especially background listeners and mothers  
**Authority:** this standard controls whenever an older role note, skill, template, or production file conflicts with it.

## 1. Declared target format

Every production branch must declare exactly one target format before its narration can pass preflight:

- `youtube-longform`
- `shorts`

The declared target format must be stored in the Automation handoff or direct-generation manifest. A missing or unrecognized target format is a blocking validation failure.

## 2. YouTube long-form runtime standard

- **Editorial target:** 8:00–10:00 of approved narration.
- **Preferred working range:** 8:15–10:30 of approved narration.
Release minimum: at least 480.000 seconds of actual approved narration audio.
- **Normal drafting range:** 1,150–1,450 spoken words.
- **Final duration authority:** the measured duration of the current Mia narration audio, not word count, a reading-speed estimate, the visual timeline, or container duration.

The operational reason for the eight-minute minimum is to keep completed monetized long-form videos eligible for mid-roll ad placement. That business goal never authorizes padding.

### Approval rule

A long-form script fails approval if its projected narration is below 8:00. After narration is generated, a measured duration below 480.000 seconds blocks alignment, visual sourcing, assembly, and release unless an explicit `short-format` exception has been approved by the human and recorded in machine-readable approval metadata.

Word count is a planning signal only. A script inside 1,150–1,450 words can still fail if Mia's actual narration is under 8:00. A script outside that range can pass only if the story remains cohesive, unpadded, and Mia's measured narration satisfies the runtime rule or an approved exception.

## 3. No-padding rule

All added duration must come from distinct, verified, research-ledger-supported story material.

### Valid expansion

- Chronology that helps a first-time listener follow the event sequence.
- Relevant personal, employment, or routine context supported by the ledger.
- Evidence explanation that states why a confirmed item mattered.
- Confirmed investigative actions and their documented results or limitations.
- Source-supported present-day status.

### Prohibited expansion

- Repeated facts or repeated evidence lists.
- Generic commentary about mysteries, time passing, or unanswered questions.
- Slowed narration or artificial pauses intended to inflate runtime.
- Filler transitions that do not advance the story.
- Speculation, theory prompts, suspect implication, or invented dramatization.
- Unsupported biography, context, dialogue, motive, or claims.

If the vetted ledger cannot support eight cohesive minutes without prohibited expansion, the case must not be forced into standard long-form.

## 4. Narrative Coherence Gate

Before human script approval, the Editor must provide a source-bound reverse outline containing:

1. Hook.
2. Essential setup.
3. Chronological events.
4. Evidence and investigation context.
5. Verified present-day status.
6. Closing.

Every outline section must state:

- Narrative purpose.
- Supporting research-ledger claim IDs.
- Transition into the next section.
- Facts intentionally excluded as repetitive, unsupported, unhelpful, or outside the research boundary.

A disconnected fact-card script fails even when every individual claim is accurate. Repetition scanning is required but cannot pass a script by itself.

The human must approve both the reverse outline and the full draft. `Script_Final.md` may be created only after that paired approval. Narration, alignment, visual sourcing, Shorts derivation, assembly, and rendering remain blocked until the approved final script exists.

## 5. Strategist viability gate

Before Writer work begins on any new case, the Strategist must evaluate the vetted research ledger—not a proposed topic alone—and record whether it can support a cohesive eight-minute episode without filler.

Required viability result:

- `Standard long-form viable` — the ledger supports distinct material for hook, setup, chronology, evidence/investigation, present status, and closing.
- `Short-Format exception — requires human approval` — the case is strong but the ledger cannot responsibly support eight minutes.
- `Backlog — insufficient long-form material` — research or narrative substance is too weak to proceed.

The viability record must identify the supported story sections, material gaps, source risks, and no-padding assessment. Writer work is blocked unless the result is `Standard long-form viable` or the human explicitly approves the documented Short-Format exception.

## 6. Shorts and TikTok standard

- **Target:** 30–60 seconds of actual narration.
- **Maximum:** 60.000 seconds unless the human explicitly approves a documented `shorts-over-60` exception.
- Use a separate, standalone, source-backed script.
- Use a completely separate licensed Orbital gameplay visual track.
- Never use or share YouTube long-form Pexels clips, case graphics, or other long-form visual assets.
- Do not invite theories, imply suspects, make uncorroborated suspect claims, or add unsupported context.
- Retain factual `[OVERLAY: ...]` cues matched to the spoken line.

## 7. Machine-checkable narration preflight

Run the backend `preflight` stage after narration generation and before alignment or assembly:

```powershell
python automation/cold_truth_pipeline.py preflight `
  --case "[CASE]" `
  --target-format youtube-longform `
  --narration-file "[PATH_TO_CURRENT_NARRATION]"
```

The backend measures the audio stream with FFprobe and writes:

`2_IN_PRODUCTION/[CASE]/Automation/preflight.json`

Required output fields include:

- `target_format`
- `narration_file`
- `narration_duration_seconds`
- `duration_source: "ffprobe_audio_stream"`
- `word_count_used_for_duration: false`
- `assembly_allowed`
- `status`
- `flags`
- validated exception metadata, when applicable

### Long-form decisions

- `< 480.000 seconds` without valid exception metadata: `blocked_under_8_minimum`; `assembly_allowed: false`.
- `< 480.000 seconds` with valid `short-format` approval: `pass_with_short_format_exception`; `assembly_allowed: true`.
- `480.000–494.999 seconds`: passes the release minimum but is flagged `below_preferred_working_range`.
- `495.000–630.000 seconds`: `pass_preferred_range`.
- `> 630.000 seconds`: passes the minimum but is flagged `above_preferred_working_range` for editorial review.

### Shorts decisions

- `< 30.000 seconds`: flagged `below_shorts_target`; not an automatic release failure.
- `30.000–60.000 seconds`: `pass_shorts_range`.
- `> 60.000 seconds` without valid approval: `blocked_over_shorts_maximum`; `assembly_allowed: false`.
- `> 60.000 seconds` with valid `shorts-over-60` approval: `pass_with_shorts_over_60_exception`.

## 8. Exception approval metadata

Exceptions require a JSON file. A note in prose, filename, word-count field, or chat history is not machine approval.

```json
{
  "case": "Case Name",
  "target_format": "youtube-longform",
  "exception_type": "short-format",
  "human_approved": true,
  "approved_by": "Brody",
  "approved_at": "YYYY-MM-DDTHH:MM:SS-04:00",
  "reason": "Specific editorial reason the case should remain shorter than eight minutes"
}
```

For a Short or TikTok above 60 seconds, use `target_format: "shorts"` and `exception_type: "shorts-over-60"`.

The preflight rejects exception metadata when the case or target format does not match, `human_approved` is not exactly `true`, the exception type is incorrect, or the approver, timestamp, or reason is blank.

## 9. Assembly hard stop

Assembly must refuse to proceed unless the current narration has a matching `preflight.json` with `assembly_allowed: true`. The preflight must reference the exact current audio path. Any script revision makes the narration and its preflight stale; regenerate the narration and rerun preflight before alignment or assembly.
