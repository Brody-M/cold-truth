# Amy pilot — M3 approval and M4 offline checks

[[2_IN_PRODUCTION/Amy Mihaljevic/Production_Summary|Amy status]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/Pilot_Runbook|Operator runbook]] · [[0_ADMIN/PROJECT_DASHBOARD|Queue]]

**2026-10-20.** M3 paired script approval is recorded from Brody's “they look good cont,” responding to the paired draft/outline review request. The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/script_approval_2026_10_20.json|approval JSON]] preserves that context and exact hashes. The [[2_IN_PRODUCTION/Amy Mihaljevic/Script_Final|final script]] differs only in title/status metadata; extracted narration matches the reviewed draft. The draft, outline, supporting inputs and original review JSON were not edited.

**Subsequent M5 update:** the [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/phase_2_narration_approval.json|one-attempt Phase 2 narration approval]] is now recorded. The original M4 snapshot below describes the state before that authorization; see the [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/narration_readiness_2026_10_20.json|current readiness checks]] for the current pre-call blocker. Zero generation submissions.

**Later provider update:** Brody then requested local speech evaluation. The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/provider_evaluation_decision_2026_10_20.json|later provider direction/hold]] is current; neither this snapshot nor the preserved Mia grant approves a replacement engine/voice.

## Evidence delivered for M4

| Requirement | Implementation / actual check |
|---|---|
| Paired approval and exact input binding | `automation/pilot_evidence.py approval`; packet, draft, outline, supporting inputs, final and spoken-text hashes verified locally |
| Actual-audio runtime gate | New direct-route `audio` command with FFprobe audio-stream duration, 30-second timeout, finite positive Decimal comparisons, exact script/audio bindings, real scope/attempt/QA receipts and rechecks after probing |
| Exceptions | Standard case/format/type/approver/time/reason metadata plus exact script/audio binding; Short-Format requires the bound summary label; no Amy exception created |
| Real-file rights and separation | New `assets` command recomputes file/evidence/review hashes, checks named track-specific rights decisions and compares IDs/source identities/canonical paths/content hashes/physical files across nonempty pools |
| Alignment interface | New `alignment` command reruns audio checks, validates transcript word coverage and finite monotonic in-bounds caption segments, requires playback receipt and exports SRT; tested with inert fixtures only |
| Tools and master procedure | FFmpeg / FFprobe 8.1.1 version checks and FFmpeg `subtitles` help inspected; no render. Manual editing, technical master probe and full playback procedure in runbook |
| Bounded narration handoff | Exact unapproved Mia settings/input/output/attempt/credit boundaries in the [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/narration_scope_proposal.json|scope proposal]] |

**Verification:** 49 tests passed; one additional symlink-escape test was skipped because this Windows account cannot create symlinks. Traversal/absolute-path rejection was tested. The strict audit resolves actual targets, but symlink creation behavior was not exercised on this machine.

The structured validation result is in `docs/pilot_m4_validation_2026_10_20.json`. The strict navigation snapshot is `docs/vault_audit_pilot_m4_2026_10_20.json`. The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/direct_generation_manifest.json|direct manifest]] appends this work pass and output hashes while retaining the October 16 entry.

## What these checks do not establish

The probe wrapper was tested using mocked stream responses, including the exact 480/60-second boundaries, nonfinite data, timeout/failure and changed inputs. Test asset/audio files were inert bytes in disposable directories, not new media. No actual Amy narration duration, media content, provider success, rights validity, perceptual alignment or creative playback has been established. No renderer/automatic assembler was added and no orchestrator state was advanced.

The minimum **offline** bridge is complete when the accompanying validation result passes. Actual account/voice access, billing within the proposed ceiling, usable generated audio, real rights and all media integration are M5/M6 evidence. A named review receipt is a record of an actual review, not a machine substitute for one. The direct route requires the operator to rerun checks immediately before its applicable downstream step and to record all work.

**Next eligible milestone: M5.** The standing Phase 2 rule in `AGENTS.md` still requires explicit media-production authorization. Script approval grants canonicalization; it does not grant a paid narration request. No Phase 2 approval has been created or consumed. There is no publishing authority.
