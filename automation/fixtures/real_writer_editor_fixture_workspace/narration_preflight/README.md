# Phase C5 synthetic narration preflight

This fixture-only area validates whether the invented C3 narration is eligible for a later, separately authorized synthetic narration test. It does not generate audio, read secrets, identify a real voice, call a provider, or authorize any production stage.

The included approval is explicitly synthetic and test-only. It is bound to the exact synthetic Writer handoff, Editor handoff, and narration-text hashes. The requested output must be a relative proposed filename beneath this directory's `output/` folder; the gate never creates that file.

`NARRATION_PREFLIGHT_PASSED` means only that the bindings, locked non-secret Mia settings, path, and denial flags are internally consistent. It does not authorize narration generation or networking.

Phase C6 adds a separate, one-time synthetic narration authorization. Its `narration_generation_authorized: true` applies only to validation of the fixture adapter. It does not authorize a provider call or audio creation during C6. The authorization binds the exact C4 approval chain, passed C5 result, locked profile, and proposed relative path. A future single synthetic provider call still requires another explicit human authorization.
