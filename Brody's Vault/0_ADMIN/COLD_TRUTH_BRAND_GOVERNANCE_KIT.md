# Cold Truth Brand and Governance Kit

## Document control

- Version: `1.0-draft-for-human-review`
- Status: `LOCAL POLICY DRAFT — NOT PRODUCTION AUTHORIZATION`
- Owner and sole human approver: `human_owner`
- Applies to: future separately approved Cold Truth planning, editorial, long-form, Shorts, packaging, and release work
- Controlling references: [[COLD_TRUTH_MASTER_EXECUTION_PLAN|Cold Truth Master Execution Plan]], [[CONTENT_FORMAT_STANDARD|Content Format Standard]], [[COLD_TRUTH_EXECUTION_STATE.json|Cold Truth Execution State]]
- Approval boundary: creating this kit does not approve a case, C3, C4, narration, sourcing, media, an account action, rendering, upload, scheduling, publishing, or production

## Channel identity

### One-sentence promise

Cold Truth tells calm, source-forward true-crime stories that separate what is known, alleged, disputed, and still unknown while treating victims and families with dignity.

### About description

Cold Truth is a faceless true-crime channel for listeners who want clear, respectful storytelling without sensationalism. Each episode builds one understandable chronology from documented sources, explains why evidence and investigative actions matter, labels uncertainty, and avoids inviting unsupported theories. Long-form episodes use case-appropriate B-roll and case graphics. Shorts are separately scripted and use an independently licensed Orbital gameplay background with factual overlays. The two visual tracks never share assets. AI may assist with structured work, but human approval, source standards, corrections, rights checks, and production gates remain mandatory.

### Primary audience

- Women ages 25–45, especially background listeners and mothers.
- Listeners who value calm delivery, clear chronology, source transparency, and respectful treatment.
- The channel never assumes the audience wants graphic detail, speculation, outrage, or theory prompts.

## Voice and language standard

### Required qualities

- Calm, plain-language, chronological, and understandable on one background listen.
- Warm without false intimacy; serious without theatrical dread.
- Precise about source strength and limits.
- Respectful toward victims, families, witnesses, communities, and unresolved uncertainty.
- Explanatory: state why a verified detail matters rather than listing disconnected facts.

### Preferred language

- “According to the charging document…”
- “Law enforcement stated…”
- “Court records show…”
- “The available record does not establish…”
- “Reports differ on this point…”
- “This claim remains unverified.”

### Prohibited framing

- Exploitative, lurid, dehumanizing, mocking, or voyeuristic language.
- Victim-blaming or unsupported judgments about a person’s choices, character, relationships, or private life.
- Declaring guilt, motive, intent, or an interior state beyond admissible support.
- Treating rumor, a tip, a private-investigator claim, or online speculation as established fact.
- Theory invitations, audience sleuthing prompts, suspect insinuation, invented dialogue, reenacted thoughts, or dramatized certainty.
- Graphic detail that is not necessary to understand the verified record.
- “Shocking,” “evil,” “you won’t believe,” “chilling secret,” or similar sensational promises.
- Padding through repetition, generic commentary, slowed narration, filler transitions, or unsupported context.

## Trust, attribution, and uncertainty

- Every future factual narration claim must map to an active claim in the vetted source ledger.
- A suspect claim may enter narration only when corroborated by law enforcement, a charging document, or a court finding.
- Allegations, conflicting accounts, and unverified information must be attributed and labeled at the point of use.
- A source’s allegation does not become a fact merely because another article repeats it.
- If support is ambiguous, exclude the claim or state the exact limitation.
- Corrections must be visible, traceable, and tied to the affected artifact and source evidence.
- AI assistance never replaces source verification or human approval and must not be presented as independent evidence.

Detailed editorial controls are in [[COLD_TRUTH_EDITORIAL_GOVERNANCE_CHECKLIST|Cold Truth Editorial Governance Checklist]].

## Visual brand brief — planning only

No logo, banner, thumbnail, graphic, or media asset is created or approved by this brief.

### Avatar/logo brief

- Simple, legible at small size, and recognizable without a face or crime-scene imagery.
- Favor restrained typography or an abstract documentary mark.
- Do not use blood, weapons, police tape, victim likenesses, suspect likenesses, fabricated evidence, or imagery that implies guilt.

### Banner brief

- Quiet documentary composition with generous negative space.
- May use the channel name and one-sentence promise only after separate design authorization.
- Must remain readable across mobile, desktop, and television safe areas.
- Must not imply a specific case, episode, suspect, crime scene, or publication schedule.

### Color direction

- Charcoal: `#14171A`
- Warm bone: `#F3EFE7`
- Muted slate: `#66717A`
- Restrained burgundy accent: `#6E2930`
- Use burgundy sparingly; never simulate blood or graphic evidence.
- Verify accessible contrast before any separately authorized final design.

### Type direction

- Use a highly legible, properly licensed sans-serif family for primary text.
- A restrained licensed serif may be used as a secondary editorial accent.
- Avoid horror, ransom-note, distressed, handwritten, or faux-evidence typography.
- Record font name, license, source, and allowed use before production.

### Thumbnail system brief

- Calm documentary hierarchy, readable at small size, with two to five words at most when text is used.
- Never imply a suspect, quote, event, relationship, discovery, or piece of evidence absent from the approved record.
- No graphic imagery, misleading faces, invented composites presented as real, or fake evidence.
- Concepts, image generation, selection, and publication each require their own applicable authorization; this kit creates none.

## Two-track brand separation

### YouTube long-form

- Exact track label: `youtube-longform`.
- Visual identity: case-appropriate landscape B-roll and restrained case graphics.
- Allowed H8 asset classes: `case_broll`, `case_graphic`.
- Orbital gameplay is prohibited.

### Orbital Shorts

- Exact track label: `shorts`.
- Visual identity: separately licensed Orbital gameplay in 9:16 with factual, speech-anchored overlays.
- Allowed H8 asset class: `orbital_gameplay`.
- Long-form B-roll and case graphics are prohibited.

No asset ID, source identity, content SHA-256, canonical path, visual file, timeline reference, or derivative may collide across tracks. Separate templates are maintained in [[COLD_TRUTH_LONG_FORM_EPISODE_TEMPLATE|Long-Form Episode Template]] and [[COLD_TRUTH_ORBITAL_SHORTS_TEMPLATE|Orbital Shorts Template]].

## Rights and license policy

- Music, footage, graphics, gameplay, fonts, models, and generated assets require a license or permission record appropriate to the intended use.
- Record creator/provider, source, terms, purchase or permission evidence where applicable, required credit, canonical local path, SHA-256, and assigned track before use.
- “Royalty-free” does not mean unlicensed; record the exact terms and retrieval date.
- Do not download, copy, transform, or use an asset merely because it is publicly viewable.
- Do not use creator videos, creator scripts, public gameplay uploads, victim social media, private-location imagery, or copyrighted reporting assets without documented authority.
- A rights uncertainty blocks sourcing, assembly, release, and fallback substitution.
- Copyright or platform claims follow the escalation procedure below; never dispute automatically.

## Naming, retention, and backup policy

- Case IDs, episode IDs, run IDs, and Short IDs must be stable, normalized, and unique before work begins.
- Recommended patterns: `case-YYYY-NNN`, `ct-ep-YYYY-NNN`, and `ct-ep-YYYY-NNN-sNN`. A pattern does not create an active ID.
- Long-form and Shorts roots remain separate: `footage/` and `shorts_gameplay/`.
- Canonical active artifacts keep path, SHA-256, approval binding, and status in the manifest.
- Superseded artifacts remain labeled `SUPERSEDED — AUDIT ONLY`; do not overwrite or reuse them as fallback.
- Preserve source ledgers, approvals, correction records, rights records, manifests, production summaries, and release evidence according to an approved retention schedule.
- Backups must preserve hashes and access controls. Test restoration separately before relying on a backup.
- Never store API keys, passwords, recovery codes, tokens, browser data, or credentials in the vault.

## Human roles and decision rights

| Role | Responsibility | Approval authority |
|---|---|---|
| Human owner | Channel direction, exceptions, paired script review, narration authority, creative approvals, render and publish decisions | Sole human approver |
| Codex coordinator | Enforce state/order, prepare bounded handoffs, validate records, stop at gates | Cannot self-approve |
| Strategist | Candidate research, source ledger, risk notes, viability | Cannot self-approve |
| Research verifier | Claim/source admissibility and conflict review | Cannot self-approve |
| Writer | Ledger-bound long-form draft | Cannot self-approve |
| Editor | Reverse outline, coherence, exclusions, factual/tonal edit | Cannot self-approve |
| Narration operator | Execute one exact approved request and create QA evidence | Cannot approve script or own execution |
| Visual producer | Long-form planning, sourcing records, licenses, visual QA | Cannot approve sourcing or master |
| Shorts editor | Standalone Short scripts, overlays, Orbital-only visual planning | Cannot approve scripts or master |
| Assembly operator | Exact-input preview, technical QA, render evidence | Cannot approve creative master or publish |
| Upload manager | Metadata, thumbnail brief, blocked upload packet | Cannot upload or publish without G09 |

One person may perform multiple operational roles, but artifacts and approvals remain separate. No operator may impersonate the human owner or translate silence, shorthand, an old file, or a passing test into approval.

## Operational separation and gates

Planning, research, verification, writing, editing, C3 paired script review, C4 narration approval, narration execution, audio QA, preflight, alignment, visual sourcing, assembly, render, packaging, upload preparation, and publishing are distinct stages.

The following always require separate, explicit authority in addition to their prerequisites:

- Any L8 synthetic execution.
- Real research or provider access.
- C3 paired script approval.
- C4 narration approval and any narration attempt.
- Audio playback/listening or other separately scoped QA when restricted by the current task.
- Long-form asset sourcing or Orbital gameplay ingest.
- Assembly and rendering.
- Thumbnail or other final visual generation.
- Account/channel/platform mutation.
- Upload, scheduling, and publishing.

No case enters production without the existing C3/C4 chain and all upstream research, viability, reverse-outline, and exact-hash prerequisites.

## H9 attempt and provider policy

- Every executable request declares one exact provider and an explicit total attempt budget of one to three.
- The budget and provider are part of the idempotency identity and may not be widened under the same request.
- Retry occurs only when the provider declares the failure retryable and unused authorized attempts remain.
- Provider, model, voice, format, path, or entrypoint fallback is prohibited.
- A nonretryable result, provider mismatch, exhausted budget, or ambiguous retry authority causes a permanent stop pending new human review.

## Account ownership and recovery checklist — no account action authorized

- [ ] The `human_owner` role is documented as the channel owner and final human authority.
- [ ] Recovery email, phone, backup codes, and ownership records are stored only in an approved secret manager or secure offline location, never this vault.
- [ ] Least privilege is assigned separately for research, asset, upload, and analytics roles.
- [ ] MFA is enabled and recovery is tested under a separately authorized account-safety task.
- [ ] OAuth scopes are minimized and reviewed before any connection.
- [ ] No shared password is placed in scripts, notes, prompts, logs, manifests, or chat.
- [ ] Account and target channel identity are reverified immediately before any authorized platform action.
- [ ] Access removal and incident response ownership are documented.

## Corrections, claims, and takedown response

1. Freeze affected downstream work; do not delete evidence or publish a silent replacement.
2. Record the report, claimant, affected artifact/path/hash, issue type, urgency, and preservation requirements.
3. Escalate privacy, safety, legal-threat, copyright, mistaken-identity, and material-fact issues to the human owner before action.
4. Compare the claim against the active source ledger, rights record, approval, and published state.
5. Record one decision: correct, update, temporarily unlist/takedown when separately authorized, dispute with evidence when separately authorized, or no change with rationale.
6. Invalidate every affected downstream artifact and approval.
7. Preserve the previous version as audit-only and document the public correction when appropriate.
8. Never contact a claimant, file a dispute, edit a platform item, unlist, delete, or republish without exact authority.

Use the blank record in [[COLD_TRUTH_APPROVAL_AND_ESCALATION_TEMPLATES|Approval and Escalation Templates]].

## Human review gate

This kit remains a draft until the human owner approves its exact version/hash. Approval of the kit will not authorize an active episode or any external action.
