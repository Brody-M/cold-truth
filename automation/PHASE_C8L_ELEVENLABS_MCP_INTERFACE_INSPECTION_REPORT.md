# Cold Truth — Phase C8l ElevenLabs MCP Interface Inspection Report

## Status

`C8L_READ_ONLY_INTERFACE_INSPECTION_COMPLETE`

## Inspection source

Only the public tool definition already exposed to Codex was inspected. No filesystem file, MCP configuration, provider configuration, environment value, credential, endpoint, account record, or prior provider result was inspected.

This report is the only file created or changed.

## Public narration-tool interface

- Server label: `ElevenLabs MCP`
- Tool name: `text_to_speech`

Documented input fields:

| Field | Type | Required |
|---|---|---:|
| `text` | string | yes |
| `voice_name` | string | no |
| `voice_id` | string or null | no |
| `model_id` | string or null | no |
| `stability` | number | no |
| `similarity_boost` | number | no |
| `style` | number | no |
| `use_speaker_boost` | boolean | no |
| `speed` | number | no |
| `language` | string | no |
| `output_format` | string | no |
| `output_directory` | string or null | no |

The public interface accepts text, voice selection and settings, output format, and an output directory. It does not expose an output-filename field or a destination-file-path field.

## Documented output classification

The documented interface indicates more than one possible output form:

- file written to a caller-provided directory;
- local file path returned through text content; or
- encoded/binary audio payload represented as an MCP audio resource.

The concrete return schema is otherwise generic, so the interface alone does not identify which form will occur for a specific invocation.

## Deterministic destination finding

The documented tool interface does **not** support a single deterministic local MP3 filename or complete destination path. It can constrain the output directory, but it cannot select the generated filename. A future design must safely account for either a returned local path or an MCP audio resource while preserving the one-operation boundary.

## Narrowest safe next step

Perform an offline C8 contract redesign for the confirmed interface. The redesigned contract should preserve one MCP operation while defining separate fail-closed handling for:

1. one returned local MP3 path contained in the authorized directory; or
2. one returned MCP audio resource written once to the exact canonical destination.

That redesign must be separately reviewed before any new live authorization. C8l authorizes no execution.

## Boundary confirmation

- MCP tool invocation: not performed
- Provider/network/API request: not performed
- New C8 authorization: not created
- Prior C8 authorization: remains consumed, count 1
- Configuration, credential, environment, endpoint, voice-ID value, account, private-file, or login-state access: not performed
- Audio/media creation, save, decode, playback, transcription, inspection, or processing: not performed
- Real-case or production access: not performed
- C9 work: not performed
- Rendering, upload, scheduling, publishing, or production activity: not performed

C3 remains `AWAITING_SCRIPT_APPROVAL`. No C4 approval was created or consumed. Publishing and real-production modes remain disabled.
