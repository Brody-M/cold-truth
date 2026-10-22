# Cold Truth Backlog

**Current routing — 2026-10-20.** Use the [[0_ADMIN/PROJECT_DASHBOARD|dashboard]] and [[0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2|maintained plan]] for work order. The July entries below are historical candidate notes; their selection labels and backend command are superseded.

| Item | Current disposition | Evidence |
|---|---|---|
| Amy Mihaljevic | M1–M4 complete; M5 local voice evaluation, unused Mia attempt held | [[2_IN_PRODUCTION/Amy Mihaljevic/Production_Summary|Summary]] |
| Springfield Three | Deferred; Short-Format exception required and not approved | [[1_IDEAS/Candidates/Springfield Three/Source_Revalidation_2026_09_05|September reassessment]] |
| Jodi Huisentruit | Backlog/history; insufficient current ledger depth | [[2_IN_PRODUCTION/Jodi Huisentruit/Editorial/Strategist_Viability_Assessment_v1|Later viability assessment]] |
| Narration-preset enforcement | Historical Mia preset retained; evaluate/select local profile before any new episode request | [[2_CHANNEL_SYSTEM/NARRATION_VOICE|Selected profile]] |

The old P1 task must not be executed against the quarantined legacy CLI. No second case should be started while the current editorial focus is in progress unless evidence forces a deliberate change.

## Historical July notes — not the current queue

## Open system items

### P1 - Enforce narration preset in the backend

**Status:** Open - code updated; verify on the next planned backend narration handoff before relying on it for production audio.

**Scope:** `automation/cold_truth_pipeline.py` must parse the exact Mia preset from `NARRATION_VOICE.md` rather than use hardcoded narration settings.

**Required verification:** Confirm a planned `voice` handoff records `eleven_multilingual_v2`, stability `0.72`, similarity boost `0.76`, style `0.05`, speed `0.94`, speaker boost `true`, and `mp3_44100_128`.

## Case shortlist - July 2026

### Jodi Huisentruit - Mason City, Iowa (1995)

**Recommendation:** Cover with adjustments - selected as Cold Truth's first real episode.

**Hook:** A morning anchor missed her shift; the public record begins with a 4:10 a.m. call and a 7:13 a.m. welfare check.

**Fit:** Source-rich, timeline-driven, and suitable for a calm, background-listener format.

**Risk flag:** Treat public theories and PI claims as unverified unless they meet the locked corroboration threshold.

**Public source base:** Iowa DCI, Mason City Police, court reporting, public dispatch records, and established regional reporting.

### Amy Mihaljevic - Bay Village, Ohio (1989)

**Research packet:** [[1_IDEAS/Candidates/Amy Mihaljevic/Source_Ledger_Draft|Source ledger]] · [[1_IDEAS/Candidates/Amy Mihaljevic/Strategist_Viability_Assessment_v1|Viability assessment]] · [[1_IDEAS/Candidates/Amy Mihaljevic/Case_Risk_Notes|Risk notes]] · [[1_IDEAS/Candidates/Amy Mihaljevic/Candidate_Scorecard|Scorecard]]

**Recommendation:** Cover with adjustments.

**Hook:** A ten-year-old was lured from a shopping center after phone calls from an unidentified man; the case remains unsolved.

**Fit:** Strong official-record base and a clear chronology.

**Risk flag:** Child victim; use exceptional restraint and exclude graphic detail or unverified person-of-interest claims.

**Public source base:** Bay Village Police, FBI reward material, Ohio Attorney General cold-case listing, and Cleveland-area news archives.

### The Springfield Three - Springfield, Missouri (1992)

**Research packet:** [[1_IDEAS/Candidates/Springfield Three/Source_Ledger_Draft|Source ledger]] · [[1_IDEAS/Candidates/Springfield Three/Strategist_Viability_Assessment_v1|Viability assessment]] · [[1_IDEAS/Candidates/Springfield Three/Case_Risk_Notes|Risk notes]] · [[1_IDEAS/Candidates/Springfield Three/Candidate_Scorecard|Scorecard]]

**Recommendation:** Cover with adjustments.

**Hook:** Three women disappeared from one home overnight after graduation celebrations and were never seen again.

**Fit:** A compelling, background-friendly timeline with official federal case material.

**Risk flag:** High rumor volume; stay tightly limited to confirmed facts and avoid popular theories.

**Public source base:** FBI ViCAP materials, Springfield Police case references, NamUs entries, and established local-news archives.
