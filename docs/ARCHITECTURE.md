# Architecture guide

## Purpose

Cold Truth keeps two related systems together:

1. An editorial vault that stores the source-backed story work for each case.
2. A Python control plane that validates handoffs and records whether a workflow may advance.

The design favors explicit inputs, immutable records, and blocked-by-default behavior over convenience. The automation can prepare and validate local artifacts; it does not quietly turn an editorial decision into a real-world action.

## Repository map

```text
Cold Truth/
├── Brody's Vault/
│   ├── 0_ADMIN/            Governing rules, role definitions, templates, approvals
│   ├── 1_IDEAS/            Backlog and candidate research packages
│   ├── 2_CHANNEL_SYSTEM/   Channel identity, voice notes, per-video workflow
│   ├── 2_IN_PRODUCTION/    Case-specific drafts, approval records, production packets
│   ├── 4_SCRIPTS/          Standalone working scripts
│   └── 5_PRODUCTION/       Local production helpers and non-final artifacts
├── automation/
│   ├── contracts/          Versioned JSON contracts and schemas
│   ├── fixtures/           Disposable synthetic test workspaces
│   ├── providers/          Narrow provider adapters and contracts
│   ├── testing/            Fake transports used only by tests
│   ├── test_*.py           Offline regression suite
│   └── orchestrator.py     Stateful workflow controller
├── skills/                 Codex role skills
└── thumbnails/             Thumbnail-prompt fixtures
```

## Control plane

`automation/orchestrator.py` coordinates deterministic case selection, contract validation, human checkpoints, append-only event records, and blocked-state reporting. It works with versioned contracts in `automation/contracts/` and isolated fixture workspaces rather than assuming a real provider is available.

The main supporting modules are:

| Component | Responsibility |
| --- | --- |
| `handoff_validator.py` | Validates structured outputs against the shared contract rules. |
| `human_approval_lifecycle.py` | Binds and validates human decisions against exact artifacts. |
| `audit_event_chain.py` | Maintains append-only, hash-linked workflow events. |
| `artifact_invalidation.py` | Marks downstream work stale when an upstream artifact changes. |
| `status_view.py` | Produces a canonical read-only view of the workflow state. |
| `cold_truth_pipeline.py` | Provides bounded local preflight operations, including measured narration checks. |
| `track_isolation.py` | Verifies that long-form and Shorts visual assets do not overlap. |

## Safety boundaries

The codebase deliberately separates **offline fixtures** from any future real execution.

- Fixture workspaces use invented cases and local fake transports.
- Provider adapters are narrow, contract-driven, and reject unapproved capabilities.
- One-time authorization contracts bind an action to exact inputs, settings, and output paths.
- Run records capture sanitized inputs, hashes, duration, exit status, and artifact identity.
- Real production remains disabled by configuration and by the governing workflow; passing a fixture does not grant production authority.

Do not treat a test report, fixture output, or adapter implementation as permission to access real cases, invoke providers, source media, render, upload, or schedule.

## Canonical state

Editorial source material is human-readable Markdown under `Brody's Vault/`. Machine handoffs for active cases live beneath that case’s `Automation/` directory. The certified orchestrator is the authority for canonical machine state; legacy helpers are intentionally quarantined from that role.

The system keeps identity and dependency links so that changing a script, approval, narration, or source record invalidates downstream work instead of allowing stale artifacts to proceed.

## Separate media branches

The long-form and short-form branches are editorially related but visually isolated:

| Branch | Permitted visual track | Required safeguard |
| --- | --- | --- |
| YouTube long-form | Case-appropriate B-roll and case graphics | Matching preflight for the current narration |
| Shorts / TikTok | Separately licensed Orbital gameplay with factual overlays | No shared visual assets with long-form |

`automation/test_track_isolation.py` protects this rule in the synthetic regression suite.

## Where to go next

- For the human editorial path, read [CONTENT_WORKFLOW.md](CONTENT_WORKFLOW.md).
- For runnable checks, read [TESTING.md](TESTING.md).
- For the detailed phase history and adapter notes, read [`automation/README.md`](../automation/README.md).
