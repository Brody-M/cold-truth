"""Canonical Cold Truth artifact dependency graph and invalidation policy."""
from __future__ import annotations

from typing import Iterable


GRAPH_VERSION = "cold_truth.artifact_dependencies.v1"

# Each key directly depends on every listed parent. Transitive invalidation is
# calculated from this one canonical graph; absent artifacts are simply ignored.
ARTIFACT_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "Research_Verification.json": ("Research_Source_Ledger.md",),
    "Script_Draft.md": ("Research_Source_Ledger.md", "Research_Verification.json", "ranked_candidates.json"),
    "Reverse_Outline.md": ("Script_Draft.md", "Research_Source_Ledger.md"),
    "Script_Draft_Reviewed.md": ("Script_Draft.md", "Reverse_Outline.md", "Research_Source_Ledger.md"),
    "checkpoint_1_packet.json": ("Reverse_Outline.md", "Script_Draft_Reviewed.md"),
    "Script_Final.md": ("Reverse_Outline.md", "Script_Draft_Reviewed.md", "checkpoint_1_packet.json"),
    "narration_descriptor.json": ("Script_Final.md",),
    "preflight.json": ("narration_descriptor.json",),
    "longform_alignment.json": ("narration_descriptor.json", "preflight.json"),
    "YouTube_Visual_Timeline.md": ("Script_Final.md", "preflight.json", "longform_alignment.json"),
    "longform_assets.json": ("Script_Final.md", "preflight.json", "longform_alignment.json", "YouTube_Visual_Timeline.md"),
    "Shorts_Package.md": ("Script_Final.md", "Research_Source_Ledger.md", "longform_assets.json"),
    "Shorts_Visual_Timeline.md": ("Shorts_Package.md",),
    "shorts_assets.json": ("Shorts_Package.md", "Shorts_Visual_Timeline.md", "Script_Final.md", "longform_assets.json"),
    "track_isolation.json": ("longform_assets.json", "shorts_assets.json"),
    "longform_assembly.json": ("narration_descriptor.json", "longform_alignment.json", "longform_assets.json", "track_isolation.json"),
    "shorts_assembly.json": ("shorts_assets.json", "track_isolation.json"),
    "checkpoint_2_packet.json": ("longform_assembly.json", "shorts_assembly.json"),
    "render_plan.json": ("checkpoint_2_packet.json", "longform_assembly.json", "shorts_assembly.json"),
    "validated_local_renders.json": ("render_plan.json",),
    "Upload_Package.md": ("Script_Final.md", "validated_local_renders.json"),
    "metadata_plan.json": ("Script_Final.md", "Research_Source_Ledger.md", "validated_local_renders.json"),
    "audit_completion.json": ("render_plan.json", "metadata_plan.json"),
}

SCRIPT_APPROVAL_BOUND = {
    "Research_Source_Ledger.md",
    "Research_Verification.json",
    "Script_Draft.md",
    "Reverse_Outline.md",
    "Script_Draft_Reviewed.md",
    "checkpoint_1_packet.json",
    "Script_Final.md",
}

ASSEMBLY_APPROVAL_BOUND = {
    "narration_descriptor.json",
    "preflight.json",
    "longform_alignment.json",
    "YouTube_Visual_Timeline.md",
    "longform_assets.json",
    "Shorts_Package.md",
    "Shorts_Visual_Timeline.md",
    "shorts_assets.json",
    "track_isolation.json",
    "longform_assembly.json",
    "shorts_assembly.json",
    "checkpoint_2_packet.json",
}


def downstream_artifacts(changed_name: str, active_names: Iterable[str]) -> list[str]:
    """Return active transitive descendants in deterministic name order."""
    active = set(active_names)
    affected = {changed_name}
    while True:
        discovered = {
            child
            for child, parents in ARTIFACT_DEPENDENCIES.items()
            if child in active and child not in affected and any(parent in affected for parent in parents)
        }
        if not discovered:
            break
        affected.update(discovered)
    affected.discard(changed_name)
    return sorted(affected)


def affected_approvals(changed_name: str, stale_names: Iterable[str]) -> list[str]:
    affected = {changed_name, *stale_names}
    approvals: list[str] = []
    if affected & SCRIPT_APPROVAL_BOUND:
        approvals.append("script_approval")
    if approvals or affected & ASSEMBLY_APPROVAL_BOUND:
        approvals.append("assembly_approval")
    return approvals


def restart_checkpoint(changed_name: str) -> str:
    if changed_name in {"Research_Source_Ledger.md", "Research_Verification.json", "ranked_candidates.json"}:
        return "RESEARCH_VERIFICATION_AND_VIABILITY"
    if changed_name in {"Script_Draft.md", "Reverse_Outline.md", "Script_Draft_Reviewed.md", "checkpoint_1_packet.json", "Script_Final.md"}:
        return "PAIRED_SCRIPT_REVIEW"
    if changed_name == "narration_descriptor.json":
        return "NARRATION_AND_RUNTIME_PREFLIGHT"
    if changed_name == "preflight.json":
        return "RUNTIME_PREFLIGHT"
    if changed_name == "longform_alignment.json":
        return "ALIGNMENT_AND_VISUAL_PLANNING"
    if changed_name in {"YouTube_Visual_Timeline.md", "longform_assets.json"}:
        return "LONGFORM_VISUAL_REVIEW"
    if changed_name in {"Shorts_Package.md", "Shorts_Visual_Timeline.md", "shorts_assets.json"}:
        return "SHORTS_REVIEW"
    return "ASSEMBLY_AND_RELEASE_REVIEW"
