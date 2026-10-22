# Cold Truth — current project assessment

**Assessed 2026-10-16.** Brody requested a whole-project reassessment and a plan that will govern subsequent work. Timeline choice: **no fixed deadline; prioritize a reliable workflow**.

[[00_START_HERE|Home]] · [[0_ADMIN/PROJECT_DASHBOARD|Current queue]] · [[0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2|Maintained plan, revision 2.1]] · [[0_ADMIN/PROJECT_REASSESSMENT_2026_09_05|Prior assessment]]

## Conclusion and actual checkpoint

The project is at **editorial preparation for a first reliable pilot**. September work advanced Amy's research and assessed it as standard-long-form viable, but stopped before producing its draft or reverse outline. Navigation/state did not record that advance. Synthetic control-plane behavior is tested; a complete real production route is not ready.

The September plan had the right broad direction, but its deliverable accounting failed: it promised draft/outline work, created links to missing files and left the queue pointing back to initial research. This revision keeps the same plan path, adds explicit milestone completion evidence and requires the dashboard, state, summary and incoming links to change together.

## Vault and connector findings

| Before repair | Evidence / implication |
|---|---|
| 72 inspected channel Markdown notes, 308 directed note links, one canvas | Baseline saved in repository `docs/vault_audit_2026_10_16_before.json` |
| Three missing targets | Amy ledger linked to nonexistent Production Summary; Amy viability linked to nonexistent draft and reverse outline |
| One undirected component, but only 68/72 reachable from Home | Both September revalidations and Amy's new ledger/viability only linked back into older hubs; ordinary forward navigation could not discover them |
| Springfield revalidation had no incoming link | Its downgrade from the old standard-viability label was hidden |
| Home/dashboard/hubs/state still described July inputs | Made completed September research appear unstarted and omitted Amy from the production shelf |
| Backlog named Jodi first and routed a backend task through the quarantined helper | Conflicted with later viability and current operating path |
| Legacy plan/kit/phase labels still sounded current | Retained evidence needed clearer routing, not a folder migration |

The connected Obsidian service successfully found and read `00_START_HERE.md` from the same vault. Local graph settings have arrows disabled; the ordered canvas and hub links are therefore the intended sequence view. No native-app screen or graph rendering was visually inspected, and graph preferences were not changed.

Implemented repairs:

- Added an honest [[2_IN_PRODUCTION/Amy Mihaljevic/Production_Summary|Amy summary]], with existing artifacts and missing deliverables stated separately. Replaced future draft/outline links with plain planned filenames.
- Updated Home, dashboard, research/production hubs, index, backlog and channel planning state together. Amy remains the single editorial focus; Springfield is deferred without an exception; Jodi is historical/backlog.
- Kept folder paths, v1/H11 approval evidence and historical media stable. Added a current-status notice above Jodi's historical completion claims.
- Improved the vault auditor to check **directed reachability from Home**, not only undirected connectivity. Tests reproduce the previously missed backlink-only-note problem.
- Updated the canvas's assessment reference and added the real Amy summary as the focused file node. Future gate labels describe dependencies rather than fictional completed files.
- Corrected narrow skill conflicts: paired approval before Shorts/visual work, aligned timing and Orbital-only Shorts, evidence-based release settings, and structural editorial repair. Updated the legacy channel-system warning and overall visual-readiness wording.

Final navigation: **74/74 inspected notes reachable from Home, 347 directed note links, one valid canvas, zero missing/ambiguous local targets and zero orphan notes**. Results are saved in `docs/vault_audit_2026_10_16_after.json` and the current `docs/vault_audit.json`. These checks validate note targets and canvas structure; they do not verify case facts, heading/block anchors or media licenses.

## Editorial inventory

| Work | Actual file evidence | Next consequence |
|---|---|---|
| Amy September research | [[1_IDEAS/Candidates/Amy Mihaljevic/Source_Revalidation_2026_09_05|Revalidation]], [[2_IN_PRODUCTION/Amy Mihaljevic/Research_Source_Ledger|26-claim ledger]], [[2_IN_PRODUCTION/Amy Mihaljevic/Editorial/Strategist_Viability_Assessment_v2|Viability v2]] | Refresh current/access-limited support; do not restart all prior research |
| Amy script packet | No draft, reverse outline, paired approval or final script | Complete M2 only after M1 reconfirms viability |
| Springfield Three | [[1_IDEAS/Candidates/Springfield Three/Source_Revalidation_2026_09_05|September assessment]] requires a Short-Format exception | Deferred; none approved |
| Jodi Huisentruit | [[2_IN_PRODUCTION/Jodi Huisentruit/Production_Summary|History]] and [[2_IN_PRODUCTION/Jodi Huisentruit/Editorial/Strategist_Viability_Assessment_v1|later nonviability assessment]] | Do not revive rejected masters or write past the current source boundary |

The last Amy retrieval record is September 5, **41 days before this audit**. Current status, reward, later developments and indexed/access-limited material require proportionate refresh. The 1,080–1,330-word planning range does not prove eight useful minutes. The funding/forensic sections need editorial scrutiny to avoid padding. No fresh external case research or source-fact certification was performed in this audit.

## Engineering reality

| Capability | Actual evidence and limit |
|---|---|
| State/approval/invalidation | Local synthetic behavior works under focused tests; this does not authorize a real case run |
| Codex role providers | Existing classes target invented fixtures; no configured real-case route follows merely from their presence |
| Narration | Selected Mia profile exists; no enabled episode narration adapter. ElevenLabs tool availability alone proves neither authority nor a tested output contract |
| Audio preflight | Legacy helper has reusable FFprobe code, but CLI writes are quarantined. It needs finite/unrounded duration handling, a probe timeout and exact script/audio binding before production use |
| Alignment | Orchestrator writes fixture timing data; real alignment path is unverified |
| Real visual assets | `automation/track_isolation.py` explicitly requires `synthetic: true` and `media_created: false`. Existing checks compare declarations; they do not certify local real-media content or licenses |
| Assembly/render | Fixture JSON descriptors exist; real render adapter is refused. Historical Jodi helpers are case-specific and some write at import, so they are not generic production integrations |
| Publishing | No automated implementation; remains disabled. A separately authorized manual upload may be a later route |
| Runtime/tools | Python, FFprobe, FFmpeg, Node and Codex launcher paths are discoverable; usable WhisperX installation and real media processing are unverified |

The read-only runtime readiness report confirms all required contracts present, no configured runtime command, all seven future adapters false, production false and publishing false. Configuration was not changed. The plan permits a bounded direct/manual pilot under the standing manifest rule once authorized, rather than making every generic adapter a prerequisite.

## Validation and limits

Focused engineering baseline passed **56/56** today: orchestrator 6, agent runtime 9, track isolation 12, human approval lifecycle 12, invalidation 7 and legacy quarantine 10. The updated navigation suite passed **13/13**, for **69 focused tests passed**. The skill-creator validator accepted all four edited skill packages. These tests and static skill checks do not prove real production readiness.

Runtime: bundled `C:/Users/brody/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`, with `-B`, from repository root. The 46 control-plane tests required a process-local temporary directory inside the writable workspace: default Windows Temp allowed writes but rejected atomic rename with WinError 5. The navigation tests also initially failed in sandbox Temp on file writes/cleanup, then passed using their own workspace-local temp root. Legacy quarantine correctly requires an outside-workspace fixture root and passed separately there. No implementation or expected test result was changed to force these passes. Workspace test temp roots were removed after checking their resolved containment.

Skill validation initially could not import PyYAML in the bundled interpreter. The installed Python 3.11 interpreter ran the same unchanged `quick_validate.py` with `-X utf8 -B` and accepted the visual-producer, Shorts-editor, upload-manager and Editor packages. No dependencies were installed.

No complete historical C/L/H regression run, paid request, media generation/playback, license recertification, account change or publication occurred. Personal-note content, credential-note content and hidden plugin/session content were outside the review. Existing uncommitted project work was preserved; backup/restore coverage, especially ignored media, is still unverified.

Approved v1 plan/hash evidence, H11 report/approval and five kit-document hashes are checked for preservation. Their old terminology is retained as history; current roles and the maintained plan resolve routine ordering. No formal human approval was invented for the revised working plan or any episode.

## Work order decision

Follow M1 source refresh → M2 full editorial packet → M3 paired review. Prepare M4 offline evidence checks during the review interval where independent. Only then request a concrete Phase 2 scope for narration and the local pilot. Review the finished local masters/package before exact publishing authority. Set a cadence after observing pilot effort, cost and rework. Detailed owners, outputs and gate conditions are in the maintained plan; the dashboard is the next-task view.
