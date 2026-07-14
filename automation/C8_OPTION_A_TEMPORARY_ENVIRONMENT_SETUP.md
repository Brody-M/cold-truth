# C8 Option A — Temporary PowerShell Session Setup

> **NOT USED FOR CURRENT C8 MCP ROUTE.** This file is retained as historical documentation only. No values were ever entered or accessed. Option A is inactive; the current future C8 route is the existing configured ElevenLabs MCP and still requires a separate explicit one-time live authorization.

## Status and boundary

Option A, temporary process-environment injection, was selected during C8g but is no longer active. Option B was never selected and remains unused.

This guide does not authorize a live C8 attempt. Do not set either variable and do not run the future C8 runner until Brody has reviewed C8g and issued a new, explicit, one-time C8 live authorization.

The values must be entered only by Brody, locally, in one newly opened Windows PowerShell session. Do not give either value to Codex. Do not ask Codex to retrieve, inspect, test, or validate a value. Do not retrieve values through instructions involving a browser or account dashboard.

## Temporary-session templates

After the separate live authorization is issued, Brody may paste these two templates into that one PowerShell window, replacing only the literal placeholders locally:

```powershell
$env:COLD_TRUTH_C8_PROVIDER_API_CREDENTIAL = '<PASTE_PROVIDER_API_KEY_HERE>'
$env:COLD_TRUTH_C8_LOCKED_VOICE_IDENTIFIER = '<PASTE_LOCKED_MIA_VOICE_ID_HERE>'
```

The later one-time runner may read only these two exact names. It must not enumerate the environment, use generic environment access, try alternate names, or read any other variable.

## Do not persist or disclose the values

- Do not use `setx`.
- Do not add either value to Windows user or system environment settings.
- Do not save either value in project files, `.env` files, `automation/private/c8_one_time_provider_config.json`, Git, logs, screenshots, chat, reports, command-history exports, or documentation.
- Do not paste either value into Codex.
- Do not print, log, serialize, hash, return, validate, copy, or report either value.
- Do not deliberately persist the values. Persistent configuration is not authorized or recommended.

The values exist only in that PowerShell process and processes it explicitly starts. After the separately authorized live attempt ends, close that PowerShell window to discard the temporary values. Do not reuse the session for production or real-case narration.

## Required sequence

1. Review and approve this C8g setup guide.
2. Issue a separate, explicit, one-time C8 live authorization.
3. Open a new Windows PowerShell window.
4. Enter the two values locally using the templates above; never send them to Codex.
5. Follow only the later live authorization's exact one-attempt instructions.
6. Close the PowerShell window immediately after the attempt.

Option A setup does not change C3, create or consume C4 approval, authorize real-case narration, or enable publishing or real production.
