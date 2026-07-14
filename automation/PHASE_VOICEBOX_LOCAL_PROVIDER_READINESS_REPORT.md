# Cold Truth — Local Tooling and Voicebox Readiness Report

Date: 2026-07-13

## Status

- Codebase Memory MCP: installed and configured for the Cold Truth repository.
- Voicebox: **BLOCKED before installation and launch** because the official Windows installer is not Authenticode-signed. The downloaded file's SHA-256 matches the official immutable GitHub release, but Windows reports `NotSigned` and no signer certificate. The task's stop rule therefore prevents execution.

## Part A — Codebase Memory MCP

- Version: `0.9.0`
- Source: official `DeusData/codebase-memory-mcp` GitHub latest release.
- Variant: standard Windows AMD64 binary; graph UI not installed.
- Binary: `C:\ColdTruthLocalTools\codebase-memory-mcp\codebase-memory-mcp.exe`
- Cache: `C:\ColdTruthLocalTools\codebase-memory-cache`
- Allowed root: exactly `C:\Youtube Automation Obsidian`
- Codex configuration: `C:\Youtube Automation Obsidian\.codex\config.toml`
- `auto_index`: `false`
- `auto_watch`: `false`
- Repository indexing performed: no
- Background watcher started: no

The upstream auto-installer was not run because it can auto-detect and modify multiple agents, MCP entries, instruction files, skills, and hooks. The verified binary was installed manually and only the project-scoped Codex configuration above was created.

## Part B — Voicebox

### Release and verification

- Version evaluated: `0.5.0`
- Source: official `jamiepine/voicebox` GitHub release.
- Downloaded installer: `C:\ColdTruthLocalTools\downloads\Voicebox_0.5.0_x64-setup.exe`
- SHA-256: `eaf5410e77946f3a76388270112bfc72925dc9d4c305b891ba600b583bc8b3b8`
- Official release SHA-256 match: yes
- Windows Authenticode status: `NotSigned`
- Signer certificate: none
- Installation performed: no
- Launch performed: no

### Hardware and backend readiness

Hardware/backend detection was not performed. Voicebox could not be launched without violating the explicit unsigned-installer stop condition. Machine suitability for local narration generation therefore remains unverified.

### Preliminary engine recommendation

If a future separately authorized, verifiable installation becomes available, the preliminary first engine to evaluate is **Kokoro 82M**. The public Voicebox documentation describes it as a small, fast engine with curated preset voices and CPU-friendly inference, making it a sensible first audition for calm English faceless narration without cloning. This is a readiness recommendation only; no model or voice was downloaded or used.

Voicebox publicly documents built-in preset voices, including curated Kokoro voices, so a preset can be evaluated instead of cloning. Voice cloning remains prohibited.

### Future integration boundary

`approved script -> local Voicebox adapter -> one bounded audio output -> preview gate`

The local adapter must explicitly control or disable:

- Automatic retries
- Async queue reprocessing
- Crash-recovery regeneration
- Auto-chunking and crossfade unless separately approved
- Voice cloning
- Text rewriting and personality-LLM behavior
- Effects processing
- MCP agent voice-output tools

### Proposed isolated offline phase

Create a new, separately authorized offline phase that defines a Voicebox adapter interface with dependency-injected fake local transport. Validate one-request limits, deterministic destination paths, exclusive-create output behavior, retry/queue prohibition, no personality rewriting, no effects, no cloning, and fail-closed handling entirely with mock responses. Do not connect the adapter to C5-C8, production, or a real Voicebox service until those offline contracts pass and a new human authorization is issued.

## Safety confirmation

- Voice profiles created or imported: zero
- Voice clones created: zero
- TTS models downloaded: zero
- Narration/audio/media generated: zero
- Voicebox local API or MCP server started: no
- Provider calls: zero
- ElevenLabs MCP or direct HTTPS route used: no
- Real-case, rendering, upload, scheduling, publishing, or production activity: none
- Historical C8/C8n authorization/audit records accessed or changed: no
- C3 remains `AWAITING_SCRIPT_APPROVAL`
- No C4 approval was created or consumed
- Publishing and real-production modes remain disabled
