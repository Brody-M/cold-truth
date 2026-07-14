# Cold Truth Editorial Governance Checklist

## Document control

- Version: `1.0-draft-for-human-review`
- Status: `BLANK REUSABLE CHECKLIST — NOT A CASE REVIEW`
- Controlling references: [[COLD_TRUTH_MASTER_EXECUTION_PLAN|Master Execution Plan]], [[CONTENT_FORMAT_STANDARD|Content Format Standard]], [[COLD_TRUTH_EXECUTION_STATE.json|Execution State]], [[COLD_TRUTH_BRAND_GOVERNANCE_KIT|Brand and Governance Kit]]
- Use only after a separately authorized case/research task. Unchecked boxes and placeholders confer no approval.

## Source-quality and corroboration standard

### Source hierarchy

1. Court findings, charging documents, filed pleadings, and official court records.
2. Law-enforcement statements, official investigative records, and other government/public records.
3. Direct records or attributable first-party material whose identity and context can be verified.
4. Reputable reporting used for context, with its underlying attribution preserved.
5. Private-investigator claims, tips, rumors, social posts, creator material, and speculation are not narration-grade evidence; use only when necessary, clearly labeled unverified, and permitted by the vetted ledger.

### Mandatory claim rules

- [ ] Every factual narration claim has a unique active ledger claim ID.
- [ ] Every ledger claim records source, source type, location, date, quote/paraphrase, admissibility, confidence, and conflicts.
- [ ] Every suspect claim is corroborated by law enforcement, a charging document, or a court finding.
- [ ] Repeated secondary coverage has not been mistaken for independent corroboration.
- [ ] Conflicting accounts are preserved side by side; the draft does not choose the more dramatic account by default.
- [ ] Unsupported or immaterial details are excluded rather than softened into implication.
- [ ] No creator script, transcript, or unsourced summary is used as evidence.

## Required statement labels

| Statement class | Required treatment |
|---|---|
| Verified fact | State plainly and bind to admissible ledger support. |
| Official allegation/charge | Attribute to the charging or official source; do not state as conviction or fact beyond the document. |
| Court finding | Identify the court or proceeding and the scope of the finding. |
| Disputed fact | State that sources differ and identify the supported limits of each account. |
| Unverified claim/tip | Label `unverified` at the point of mention and explain why it is included; omit if it does not serve a necessary verified purpose. |
| Opinion/analysis | Attribute the speaker and keep separate from factual narration. |
| Unknown | State that the available record does not establish the answer. |
| Inference | Use only when logically necessary, explicitly labeled, and supported by cited facts; never infer guilt, motive, or private thought. |

## Viability and narrative coherence gate

- [ ] A vetted source ledger exists before viability assessment.
- [ ] The Strategist records exactly one allowed viability result.
- [ ] Standard long-form can support hook, setup, chronology, investigation/evidence context, verified status, and conclusion without padding.
- [ ] Any Short-Format exception is explicit, machine-documented, and human-approved before Writer work.
- [ ] The Editor created a reverse outline with purpose, claim support, transition, and exclusions for every section.
- [ ] The full draft forms one understandable spoken story for a first-time background listener.
- [ ] Repetition scanning occurred but was not treated as sufficient editorial review.
- [ ] Added runtime comes only from distinct ledger-supported substance.
- [ ] The exact reverse outline and exact full draft are ready for paired C3 review.

## Privacy, dignity, and sensitive-subject review

- [ ] Names, ages, relationships, locations, medical details, family details, and identifying context are necessary and source-supported.
- [ ] Minors and private individuals receive heightened minimization.
- [ ] Home addresses, live location clues, contact data, account credentials, and other dangerous personal data are excluded.
- [ ] Sexual violence, child harm, suicide, addiction, mental health, domestic violence, and graphic injury are described only as necessary and without lurid detail.
- [ ] Victim behavior is not framed as causing or inviting harm.
- [ ] No person’s silence, emotion, lifestyle, relationship, or online activity is used to imply guilt without admissible support.
- [ ] Images and graphics do not expose a private location, misidentify a person, fabricate evidence, or create a misleading association.
- [ ] Current legal status, presumption of innocence, acquittal/dismissal, and unresolved status are accurately represented where applicable.
- [ ] Any meaningful privacy, safety, mistaken-identity, or legal risk is escalated to the human owner before drafting or production.

## Legal-risk review

- [ ] Defamation risk: every damaging claim has admissible support, exact attribution, and current status.
- [ ] Contempt/fair-trial risk: active proceeding restrictions and jurisdictional limits are identified.
- [ ] Copyright risk: quotes and media use are limited, necessary, licensed or otherwise reviewed, and accurately attributed.
- [ ] Privacy/publicity risk: private facts and likeness use are necessary, proportionate, and reviewed.
- [ ] Safety risk: the work does not direct harassment, doxxing, amateur investigation, or contact with involved people.
- [ ] The content does not invite theories, name unsupported suspects, or encourage viewers to solve the case.
- [ ] High-risk uncertainty is escalated; the team does not improvise legal conclusions.

This checklist is governance, not legal advice. Material legal uncertainty requires qualified human review.

## Corrections, updates, takedowns, and escalation

### Intake

- [ ] Preserve the report and affected artifact; do not silently overwrite or delete.
- [ ] Record reporter/claimant only to the minimum necessary extent.
- [ ] Record exact affected path/hash, statement/timestamp, issue class, evidence supplied, and urgency.
- [ ] Freeze affected downstream work and publication actions.

### Decision classes

- `CORRECTION_REQUIRED`
- `UPDATE_REQUIRED`
- `TEMPORARY_HOLD_REQUIRES_AUTHORIZATION`
- `TAKEDOWN_REQUIRES_AUTHORIZATION`
- `RIGHTS_DISPUTE_REQUIRES_AUTHORIZATION`
- `NO_CHANGE_WITH_RECORDED_RATIONALE`
- `ESCALATE_FOR_QUALIFIED_REVIEW`

### Resolution

- [ ] The human owner approved the exact decision when it affects an active or published artifact.
- [ ] Upstream changes invalidated every affected script, narration, timing, visual, metadata, approval, render, and upload packet.
- [ ] Previous versions remain `SUPERSEDED — AUDIT ONLY`.
- [ ] A visible correction/update is prepared when appropriate, but no platform action occurs without authority.
- [ ] Rights claims are not automatically disputed, conceded, deleted, or counter-notified.
- [ ] The correction/escalation record is complete and linked.

## C3/C4 and production hard stop

- [ ] C3 paired script approval binds the exact reverse-outline path/hash and full-draft path/hash.
- [ ] `Script_Final.md` does not exist until the exact C3 approval is valid and consumed once.
- [ ] C4 binds the exact final script hash, provider/model/voice/settings, target format, canonical output path, attempt budget, and no-fallback rule.
- [ ] C3 does not authorize C4, narration, playback, sourcing, media, render, or publication.
- [ ] C4 does not authorize visuals, render, upload, scheduling, publishing, retries beyond budget, or fallback.
- [ ] No case enters production unless both required approvals and every upstream gate are current.

## Final checklist disposition — leave blank until an authorized review

- Review ID: `[BLANK]`
- Episode ID: `[BLANK]`
- Reviewer: `[BLANK]`
- Result: `[BLANK — PASS / FAIL / ESCALATE]`
- Blocking items: `[BLANK]`
- Exact next allowed action: `[BLANK]`
- Approval reference, if separately created: `[BLANK]`

Completing this checklist does not itself create C3, C4, or production authority.
