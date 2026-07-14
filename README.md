# Cold Truth

### A structured creative-production toolkit for research-led video storytelling.

Cold Truth brings together an Obsidian-friendly editorial workspace, reusable role guides, and a local Python automation layer. It is designed to make a complex video workflow easier to understand, review, and maintain—from early research through approved production planning.

> **Project status:** local-first and safety-conscious. The repository documents and validates the workflow; it does not publish content or perform production actions automatically.

## What it includes

| | Area | What it does |
| :--: | --- | --- |
| 🗂️ | **Editorial vault** | Organizes ideas, research, scripts, production packets, templates, and channel documentation in Markdown. |
| ⚙️ | **Automation layer** | Validates structured handoffs, workflow state, approvals, asset separation, and audit records. |
| 🧩 | **Role skills** | Provides focused instructions for strategy, writing, editing, visual planning, short-form work, and metadata. |
| 🧪 | **Fixture suite** | Exercises workflow rules with synthetic, disposable examples rather than live production work. |

## How it works

```mermaid
flowchart LR
    A[Research] --> B[Story planning]
    B --> C[Writing & editorial review]
    C --> D[Human approval]
    D --> E[Preflight & production planning]
    E --> F[Human-authorized production]
```

The system is built around a few simple principles:

- Keep research, drafts, and approvals traceable.
- Treat quality gates as explicit checkpoints, not assumptions.
- Keep long-form and short-form visual assets in separate tracks.
- Validate local workflow behavior with reproducible fixtures.
- Require human authorization before any real production action.

## Explore the project

- [Architecture guide](docs/ARCHITECTURE.md) — a map of the vault, control plane, contracts, and safety boundaries.
- [Editorial workflow](docs/CONTENT_WORKFLOW.md) — the path from a research package to an approved production plan.
- [Testing guide](docs/TESTING.md) — safe local checks and the scope of the fixture suite.
- [Automation reference](automation/README.md) — implementation notes and phase-by-phase validation history.
- [Vault index](<Brody's Vault/0_ADMIN/VAULT_INDEX.md>) — a guide to the editorial workspace.

## Repository layout

```text
├── Brody's Vault/   Editorial workspace and production templates
├── automation/      Python control plane, schemas, fixtures, and tests
├── skills/          Reusable role-specific Codex skills
├── thumbnails/      Thumbnail prompt fixtures
└── docs/            Public-facing project guides
```

## Local validation

The project uses standalone Python test modules and synthetic fixture data. A few useful starting points:

```powershell
python -B automation/test_orchestrator.py
python -B automation/test_track_isolation.py
python -B automation/test_script_approval_gate.py
```

For the broader validation matrix and runtime notes, see [docs/TESTING.md](docs/TESTING.md).

## Contributing

Contributions that improve clarity, workflow safety, documentation, or fixture coverage are welcome. Before proposing a change, review [`AGENTS.md`](AGENTS.md), keep generated media and credentials out of version control, and run the relevant local checks.
