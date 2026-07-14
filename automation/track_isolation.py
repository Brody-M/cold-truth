"""Canonical long-form/Shorts visual-track validation with zero asset reuse."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ASSET_MANIFEST_SCHEMA_VERSION = "cold_truth.asset_manifest.v1"
TRACK_ISOLATION_SCHEMA_VERSION = "cold_truth.track_isolation.v1"
LONGFORM_TRACK = "youtube-longform"
SHORTS_TRACK = "shorts"
TRACK_ASSET_CLASSES = {
    LONGFORM_TRACK: {"case_broll", "case_graphic"},
    SHORTS_TRACK: {"orbital_gameplay"},
}


class TrackIsolationError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_manifest(manifest: Any, expected_track: str) -> dict[str, set[str]]:
    if not isinstance(manifest, dict):
        raise TrackIsolationError(f"{expected_track} asset manifest must be an object")
    if manifest.get("schema_version") != ASSET_MANIFEST_SCHEMA_VERSION:
        raise TrackIsolationError(f"{expected_track} asset manifest schema mismatch")
    if manifest.get("track") != expected_track:
        raise TrackIsolationError(f"Asset manifest track mismatch: expected {expected_track}")
    if manifest.get("shared_assets_allowed") is not False:
        raise TrackIsolationError(f"{expected_track} must declare shared_assets_allowed false")
    if manifest.get("synthetic") is not True or manifest.get("media_created") is not False:
        raise TrackIsolationError(f"{expected_track} H8 manifest must remain synthetic with no media")
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        raise TrackIsolationError(f"{expected_track} assets must be a nonempty array")

    identities: dict[str, set[str]] = {
        "asset_id": set(),
        "source_identity": set(),
        "content_sha256": set(),
        "canonical_path": set(),
    }
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            raise TrackIsolationError(f"{expected_track} asset {index} must be an object")
        asset_id = asset.get("asset_id")
        source_identity = asset.get("source_identity")
        if not isinstance(asset_id, str) or not asset_id.strip():
            raise TrackIsolationError(f"{expected_track} asset {index} missing asset_id")
        if not isinstance(source_identity, str) or not source_identity.strip():
            raise TrackIsolationError(f"{expected_track} asset {asset_id} missing source_identity")
        if asset.get("track") != expected_track:
            raise TrackIsolationError(f"Asset track mismatch: {asset_id}")
        if asset.get("asset_class") not in TRACK_ASSET_CLASSES[expected_track]:
            raise TrackIsolationError(f"Prohibited asset class for {expected_track}: {asset_id}")
        if asset.get("status") != "ready" or asset.get("local_record") is not True or asset.get("licensed_record") is not True:
            raise TrackIsolationError(f"Incomplete asset record for {expected_track}: {asset_id}")
        for kind, value in (("asset_id", asset_id), ("source_identity", source_identity)):
            if value in identities[kind]:
                raise TrackIsolationError(f"Duplicate {kind} within {expected_track}: {value}")
            identities[kind].add(value)
        content_hash = asset.get("content_sha256")
        if content_hash is not None:
            if not isinstance(content_hash, str) or len(content_hash) != 64 or any(character not in "0123456789abcdef" for character in content_hash):
                raise TrackIsolationError(f"Invalid content_sha256 for {expected_track}: {asset_id}")
            if content_hash in identities["content_sha256"]:
                raise TrackIsolationError(f"Duplicate content_sha256 within {expected_track}: {content_hash}")
            identities["content_sha256"].add(content_hash)
        canonical_path = asset.get("canonical_path")
        if canonical_path is not None:
            if not isinstance(canonical_path, str):
                raise TrackIsolationError(f"Invalid canonical_path for {expected_track}: {asset_id}")
            path = Path(canonical_path)
            if not path.is_absolute() or canonical_path != str(path.resolve()):
                raise TrackIsolationError(f"Noncanonical asset path for {expected_track}: {asset_id}")
            if canonical_path in identities["canonical_path"]:
                raise TrackIsolationError(f"Duplicate canonical_path within {expected_track}: {canonical_path}")
            identities["canonical_path"].add(canonical_path)
    return identities


def build_track_isolation_report(longform_path: Path, shorts_path: Path) -> dict[str, Any]:
    try:
        longform = json.loads(longform_path.read_text(encoding="utf-8"))
        shorts = json.loads(shorts_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise TrackIsolationError("Cannot read canonical asset manifests") from exc

    long_identities = _validate_manifest(longform, LONGFORM_TRACK)
    short_identities = _validate_manifest(shorts, SHORTS_TRACK)
    collisions = [
        {"identity_kind": kind, "identity": value}
        for kind in sorted(long_identities)
        for value in sorted(long_identities[kind] & short_identities[kind])
    ]
    return {
        "schema_version": TRACK_ISOLATION_SCHEMA_VERSION,
        "longform_track": LONGFORM_TRACK,
        "shorts_track": SHORTS_TRACK,
        "longform_manifest_sha256": _sha256(longform_path),
        "shorts_manifest_sha256": _sha256(shorts_path),
        "longform_asset_count": len(longform["assets"]),
        "shorts_asset_count": len(shorts["assets"]),
        "shared_asset_count": len(collisions),
        "shared_asset_identities": collisions,
        "shared_assets_allowed": False,
        "passed": not collisions,
        "media_inspected": False,
        "media_created": False,
    }
