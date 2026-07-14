# Phase C1.3 Schema Compatibility Report

**Date:** 2026-07-11  
**Scope:** Disposable C1 fixture, offline validation only  
**Codex invocation:** Not authorized and not run

## Issues found

1. `schema_version` and numerous other constant-valued properties had no explicit JSON Schema `type`.
2. String, integer, and boolean constants relied on `const` alone rather than a typed constraint.
3. Object-valued constants (`score_breakdown`, `artifact_hashes`, and `runtime`) did not expose typed `properties`, complete `required` lists, or recursively testable child schemas.
4. `inputs.items` declared only `type: object`; it had no properties, required fields, or `additionalProperties: false` boundary.
5. Empty output, warning, error, and tool-call arrays had no typed `items` schema.
6. Decision records and result claim arrays were represented as whole-value constants rather than typed item/object schemas.
7. The local validator did not evaluate `anyOf`; a heterogeneous input-record schema could therefore pass locally without its selected branch being checked.
8. There was no offline compatibility pass enforcing explicit property types, complete object requirements, `additionalProperties: false`, typed array items, supported keywords, or enum/type agreement.

## Compatibility repair

- Every output property now has an explicit primitive, array, or object type.
- Fixed primitive values use typed singleton enums; the ordered three-item claim lists additionally use a typed exact-value constraint.
- Every object has explicit `properties`, a complete `required` array, and `additionalProperties: false`.
- Every array has a typed `items` schema.
- The three heterogeneous input records use one necessary non-nullable `anyOf`, with each branch fully typed and closed.
- Synthetic case identity, claims, viability, score, risk, disposition, empty outputs/tools, and disabled publishing remain enforced.
- Local contract equality continues to enforce the exact supplied input values and hashes.
- The local subset validator now evaluates `anyOf` and includes a strict schema-compatibility checker.

## Offline result

Fifteen tests passed and zero failed. No real invocation, Codex process, transport, model, network, external tool, real-case access, media action, render, upload, scheduling, publishing, or real-production action occurred.

Remote structured-output acceptance remains unverified and requires separate authorization for exactly one fresh C1 fixture invocation.

## Phase C1.4 remote normalization

The remote endpoint rejected the canonical array-valued claim `const`. The remote schema now represents each fixed ordered claim as a required typed scalar field:

```text
claim_1: string enum [SYN-C1-01]
claim_2: string enum [SYN-C1-02]
claim_3: string enum [SYN-C1-03]
```

This representation is used in both the result and the echoed synthetic candidate input. A fixture-only deterministic normalizer verifies both three-field sequences, removes the scalar fields, and reconstructs the canonical `claim_ids` arrays. Missing, altered, duplicated, reordered, or additional claim fields are not repaired; they block validation.

The remote subset checker now rejects array/object-valued constants or enum members, tuple-style items, array cardinality/containment keywords, unsupported composition/conditionals, recursive references, untyped properties, open objects, unknown keywords, and root-level `anyOf`. The original strict canonical schema remains separate and continues to enforce exact arrays, empty outputs/tools, hashes, fixed values, and disabled publishing after normalization.

Seventeen offline tests passed. `real_invocation` remained `not_requested`.
