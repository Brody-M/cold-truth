"""L6 guarded binding to the sealed Piper runtime.

This module permits locked identity checks, one CPU-only session load, and safe
session metadata inspection. It deliberately exposes no inference-capable or
output-capable public API.
"""
from __future__ import annotations

import gc
import hashlib
import json
import os
import stat
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Literal

import onnxruntime
from piper.voice import PiperVoice

from providers.piper_local_adapter_contract import (
    LOCKED_ENGINE_VERSION as L2_LOCKED_ENGINE_VERSION,
    LOCKED_MODEL_ID as L2_LOCKED_MODEL_ID,
    LOCKED_MODEL_SOURCE_MARKER as L2_LOCKED_MODEL_SOURCE_MARKER,
    ROUTE_IDENTIFIER as L2_ROUTE_IDENTIFIER,
    SUPPORTED_FUTURE_OUTPUT_FORMAT as L2_FUTURE_OUTPUT_FORMAT,
)


SEALED_INTERPRETER = Path(
    r"C:\ColdTruthLocalTools\piper-1.4.2-venv\Scripts\python.exe"
)
LOCKED_ASSET_ROOT = Path(r"C:\ColdTruthLocalTools\piper-1.4.2-assets")
LOCKED_MODEL_PATH = LOCKED_ASSET_ROOT / "en_US-ljspeech-high.onnx"
LOCKED_CONFIG_PATH = LOCKED_ASSET_ROOT / "en_US-ljspeech-high.onnx.json"
LOCKED_PIPER_VERSION = "1.4.2"
LOCKED_ONNXRUNTIME_VERSION = "1.27.0"
LOCKED_MODEL_ID = "en_US-ljspeech-high"
LOCKED_MODEL_SHA256 = (
    "5d4f08ba6a2a48c44592eed3ce56bf85e9de3dd4e20df90541ae68a8310c029a"
)
LOCKED_CONFIG_SHA256 = (
    "7e1f4634af596d83cca997fb7a931ba80b70f8a316a2655ee69c55365e0ace14"
)
LOCKED_PROVIDER = "CPUExecutionProvider"
L6_PROBE_MARKER = "l6_no_text_binding_probe"
L6_PROBE_KIND = "l6_fake_binding_probe"

FORBIDDEN_OPERATION_CATEGORIES = (
    "text_input",
    "phoneme_input",
    "tensor_input",
    "scales_input",
    "input_lengths",
    "voice_override",
    "onnx_run",
    "onnx_run_with_iobinding",
    "profiling",
    "warm_up",
    "benchmark",
    "synthesis",
    "stream",
    "phonemization",
    "output_write",
    "output_path",
    "cli",
    "subprocess",
    "local_server",
    "queue",
    "retry",
    "fallback",
    "auto_chunking",
    "polling",
    "background_task",
    "cleanup",
    "copy",
    "rename",
    "overwrite",
    "second_runtime_initialization",
    "real_writer_attachment",
)

BlockedOperation = Literal[
    "text_input",
    "phoneme_input",
    "tensor_input",
    "scales_input",
    "input_lengths",
    "voice_override",
    "onnx_run",
    "onnx_run_with_iobinding",
    "profiling",
    "warm_up",
    "benchmark",
    "synthesis",
    "stream",
    "phonemization",
    "output_write",
    "output_path",
    "cli",
    "subprocess",
    "local_server",
    "queue",
    "retry",
    "fallback",
    "auto_chunking",
    "polling",
    "background_task",
    "cleanup",
    "copy",
    "rename",
    "overwrite",
    "second_runtime_initialization",
    "real_writer_attachment",
]


@dataclass(frozen=True, slots=True)
class GuardedRuntimeIdentity:
    interpreter_path: str
    engine_version: str
    onnxruntime_version: str
    model_id: str
    model_path: str
    config_path: str
    model_sha256: str
    config_sha256: str
    provider: str


@dataclass(frozen=True, slots=True)
class SafeTensorMetadata:
    name: str
    shape: tuple[object, ...]
    tensor_type: str


@dataclass(frozen=True, slots=True)
class GuardedSessionMetadata:
    active_providers: tuple[str, ...]
    available_providers: tuple[str, ...]
    inputs: tuple[SafeTensorMetadata, ...]
    outputs: tuple[SafeTensorMetadata, ...]
    config_structure_valid: bool
    asset_inventory_unchanged: bool


@dataclass(frozen=True, slots=True)
class GuardedRuntimeLedger:
    safe_operations: tuple[str, ...]
    blocked_by_category: tuple[tuple[str, int], ...]
    blocked_operation_count: int
    runtime_initializations: int
    identity_inspections: int
    text_inputs: int
    inference_calls: int
    synthesis_calls: int
    phonemization_calls: int
    output_writes: int


@dataclass(frozen=True, slots=True)
class L6BindingProbe:
    probe_kind: str
    probe_marker: str
    route_identifier: str
    engine_version: str
    model_id: str
    model_source_marker: str
    future_output_format: str


BindingStatus = Literal["bound", "rejected"]
BindingError = Literal[
    "invalid_probe_type",
    "non_fake_request_path",
    "invalid_probe_marker",
    "route_mismatch",
    "engine_version_mismatch",
    "model_id_mismatch",
    "model_source_mismatch",
    "future_output_format_mismatch",
    "runtime_identity_mismatch",
]


@dataclass(frozen=True, slots=True)
class L6BindingResult:
    status: BindingStatus
    safe_error_category: BindingError | None
    route_identifier: str
    engine_version: str
    model_id: str
    future_output_format: str
    output_handling_available: bool
    runtime_interaction_count: int


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _locked_regular_file(path: Path, root: Path) -> None:
    file_info = os.lstat(path)
    attributes = getattr(file_info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if not stat.S_ISREG(file_info.st_mode):
        raise RuntimeError("locked_asset_not_regular")
    if stat.S_ISLNK(file_info.st_mode) or attributes & reparse:
        raise RuntimeError("locked_asset_is_link_or_reparse")
    if path.resolve(strict=True).parent != root.resolve(strict=True):
        raise RuntimeError("locked_asset_outside_root")


def _validate_config_structure(path: Path) -> None:
    with path.open("r", encoding="utf-8") as config_handle:
        config = json.load(config_handle)

    required_types = {
        "dataset": str,
        "audio": dict,
        "espeak": dict,
        "language": dict,
        "inference": dict,
        "phoneme_type": str,
        "phoneme_map": dict,
        "phoneme_id_map": dict,
        "num_symbols": int,
        "num_speakers": int,
        "speaker_id_map": dict,
        "piper_version": str,
    }
    if type(config) is not dict:
        raise RuntimeError("locked_config_invalid")
    for field, expected_type in required_types.items():
        if field not in config or not isinstance(config[field], expected_type):
            raise RuntimeError("locked_config_invalid")

    if (
        config["dataset"] != "ljspeech"
        or config["audio"].get("sample_rate") != 22050
        or config["audio"].get("quality") != "high"
        or config["language"].get("code") != "en_US"
        or config["num_speakers"] != 1
    ):
        raise RuntimeError("locked_config_identity_mismatch")


class GuardedPiperRuntime:
    """One-process, one-initialization, metadata-only Piper wrapper."""

    __slots__ = (
        "_identity",
        "_initialization_attempted",
        "_initialized",
        "_voice",
        "_session_metadata",
        "_safe_operations",
        "_blocked_counts",
        "_identity_inspections",
    )

    _process_runtime_initializations = 0

    def __init__(
        self,
        *,
        interpreter_path: Path,
        engine_version: str,
        model_id: str,
        model_path: Path,
        config_path: Path,
        model_sha256: str,
        config_sha256: str,
        provider: str,
    ) -> None:
        declared = (
            Path(interpreter_path),
            engine_version,
            model_id,
            Path(model_path),
            Path(config_path),
            model_sha256,
            config_sha256,
            provider,
        )
        expected = (
            SEALED_INTERPRETER,
            LOCKED_PIPER_VERSION,
            LOCKED_MODEL_ID,
            LOCKED_MODEL_PATH,
            LOCKED_CONFIG_PATH,
            LOCKED_MODEL_SHA256,
            LOCKED_CONFIG_SHA256,
            LOCKED_PROVIDER,
        )
        if declared != expected:
            raise ValueError("locked_runtime_identity_mismatch")

        self._identity = GuardedRuntimeIdentity(
            interpreter_path=str(SEALED_INTERPRETER),
            engine_version=LOCKED_PIPER_VERSION,
            onnxruntime_version=LOCKED_ONNXRUNTIME_VERSION,
            model_id=LOCKED_MODEL_ID,
            model_path=str(LOCKED_MODEL_PATH),
            config_path=str(LOCKED_CONFIG_PATH),
            model_sha256=LOCKED_MODEL_SHA256,
            config_sha256=LOCKED_CONFIG_SHA256,
            provider=LOCKED_PROVIDER,
        )
        self._initialization_attempted = False
        self._initialized = False
        self._voice: PiperVoice | None = None
        self._session_metadata: GuardedSessionMetadata | None = None
        self._safe_operations: list[str] = []
        self._blocked_counts = {
            category: 0 for category in FORBIDDEN_OPERATION_CATEGORIES
        }
        self._identity_inspections = 0

    @classmethod
    def exact_locked(cls) -> "GuardedPiperRuntime":
        return cls(
            interpreter_path=SEALED_INTERPRETER,
            engine_version=LOCKED_PIPER_VERSION,
            model_id=LOCKED_MODEL_ID,
            model_path=LOCKED_MODEL_PATH,
            config_path=LOCKED_CONFIG_PATH,
            model_sha256=LOCKED_MODEL_SHA256,
            config_sha256=LOCKED_CONFIG_SHA256,
            provider=LOCKED_PROVIDER,
        )

    @classmethod
    def process_runtime_initialization_count(cls) -> int:
        return cls._process_runtime_initializations

    def initialize_and_inspect(self) -> GuardedSessionMetadata:
        if self._initialization_attempted or type(self)._process_runtime_initializations:
            self.reject_operation("second_runtime_initialization")
            raise RuntimeError("second_runtime_initialization_blocked")
        self._initialization_attempted = True

        if Path(sys.executable).resolve() != SEALED_INTERPRETER.resolve(strict=True):
            raise RuntimeError("sealed_interpreter_mismatch")
        if metadata.version("piper-tts") != LOCKED_PIPER_VERSION:
            raise RuntimeError("piper_version_mismatch")
        if metadata.version("onnxruntime") != LOCKED_ONNXRUNTIME_VERSION:
            raise RuntimeError("onnxruntime_version_mismatch")
        self._safe_operations.append("runtime_versions_verified")

        root = LOCKED_ASSET_ROOT.resolve(strict=True)
        inventory_before = tuple(sorted(item.name for item in root.iterdir()))
        if inventory_before != (
            "en_US-ljspeech-high.onnx",
            "en_US-ljspeech-high.onnx.json",
        ):
            raise RuntimeError("unexpected_locked_asset_inventory")

        _locked_regular_file(LOCKED_MODEL_PATH, root)
        _locked_regular_file(LOCKED_CONFIG_PATH, root)
        if _sha256_file(LOCKED_MODEL_PATH) != LOCKED_MODEL_SHA256:
            raise RuntimeError("model_hash_mismatch")
        if _sha256_file(LOCKED_CONFIG_PATH) != LOCKED_CONFIG_SHA256:
            raise RuntimeError("config_hash_mismatch")
        _validate_config_structure(LOCKED_CONFIG_PATH)
        self._safe_operations.append("locked_assets_verified")

        available = tuple(onnxruntime.get_available_providers())
        if LOCKED_PROVIDER not in available:
            raise RuntimeError("cpu_provider_unavailable")

        self._voice = PiperVoice.load(
            model_path=LOCKED_MODEL_PATH,
            config_path=LOCKED_CONFIG_PATH,
            use_cuda=False,
            download_dir=LOCKED_ASSET_ROOT,
        )
        session = self._voice.session
        active = tuple(session.get_providers())
        if active != (LOCKED_PROVIDER,):
            raise RuntimeError("non_cpu_provider_active")

        inputs = tuple(
            SafeTensorMetadata(
                name=item.name,
                shape=tuple(item.shape),
                tensor_type=item.type,
            )
            for item in session.get_inputs()
        )
        outputs = tuple(
            SafeTensorMetadata(
                name=item.name,
                shape=tuple(item.shape),
                tensor_type=item.type,
            )
            for item in session.get_outputs()
        )
        if not inputs or not outputs:
            raise RuntimeError("session_metadata_missing")

        inventory_after = tuple(sorted(item.name for item in root.iterdir()))
        if inventory_after != inventory_before:
            raise RuntimeError("unexpected_runtime_artifact")

        self._session_metadata = GuardedSessionMetadata(
            active_providers=active,
            available_providers=available,
            inputs=inputs,
            outputs=outputs,
            config_structure_valid=True,
            asset_inventory_unchanged=True,
        )
        self._initialized = True
        type(self)._process_runtime_initializations += 1
        self._safe_operations.extend(
            ("cpu_session_initialized", "session_metadata_inspected")
        )
        return self._session_metadata

    def safe_identity(self) -> GuardedRuntimeIdentity:
        if not self._initialized:
            raise RuntimeError("runtime_not_initialized")
        self._identity_inspections += 1
        self._safe_operations.append("binding_identity_inspected")
        return self._identity

    def session_metadata(self) -> GuardedSessionMetadata:
        if not self._initialized or self._session_metadata is None:
            raise RuntimeError("runtime_not_initialized")
        return self._session_metadata

    def reject_operation(self, operation: BlockedOperation) -> None:
        if type(operation) is not str or operation not in self._blocked_counts:
            raise ValueError("unknown_guarded_operation_category")
        self._blocked_counts[operation] += 1
        self._safe_operations.append(f"blocked:{operation}")

    def ledger_snapshot(self) -> GuardedRuntimeLedger:
        blocked = tuple(
            (category, self._blocked_counts[category])
            for category in FORBIDDEN_OPERATION_CATEGORIES
            if self._blocked_counts[category]
        )
        return GuardedRuntimeLedger(
            safe_operations=tuple(self._safe_operations),
            blocked_by_category=blocked,
            blocked_operation_count=sum(self._blocked_counts.values()),
            runtime_initializations=1 if self._initialized else 0,
            identity_inspections=self._identity_inspections,
            text_inputs=0,
            inference_calls=0,
            synthesis_calls=0,
            phonemization_calls=0,
            output_writes=0,
        )

    def _release_at_process_exit(self) -> None:
        """Private reference release used only by the test process epilogue."""
        self._voice = None
        self._session_metadata = None
        gc.collect()


class L6AdapterRuntimeBindingValidator:
    """No-text validator binding immutable L2 identifiers to L6 identity."""

    __slots__ = ("_runtime", "_runtime_interaction_count")

    def __init__(self, *, guarded_runtime: GuardedPiperRuntime) -> None:
        if type(guarded_runtime) is not GuardedPiperRuntime:
            raise TypeError("L6 accepts only GuardedPiperRuntime")
        self._runtime = guarded_runtime
        self._runtime_interaction_count = 0

    def validate_probe(self, probe: object) -> L6BindingResult:
        category: BindingError | None = None
        if type(probe) is not L6BindingProbe:
            category = "invalid_probe_type"
        elif probe.probe_kind != L6_PROBE_KIND:
            category = "non_fake_request_path"
        elif probe.probe_marker != L6_PROBE_MARKER:
            category = "invalid_probe_marker"
        elif probe.route_identifier != L2_ROUTE_IDENTIFIER:
            category = "route_mismatch"
        elif probe.engine_version != L2_LOCKED_ENGINE_VERSION:
            category = "engine_version_mismatch"
        elif probe.model_id != L2_LOCKED_MODEL_ID:
            category = "model_id_mismatch"
        elif probe.model_source_marker != L2_LOCKED_MODEL_SOURCE_MARKER:
            category = "model_source_mismatch"
        elif probe.future_output_format != L2_FUTURE_OUTPUT_FORMAT:
            category = "future_output_format_mismatch"

        if category is not None:
            return self._result("rejected", category)

        identity = self._runtime.safe_identity()
        self._runtime_interaction_count += 1
        if (
            identity.engine_version != L2_LOCKED_ENGINE_VERSION
            or identity.model_id != L2_LOCKED_MODEL_ID
            or identity.provider != LOCKED_PROVIDER
        ):
            return self._result("rejected", "runtime_identity_mismatch")
        return self._result("bound", None)

    def _result(
        self,
        status: BindingStatus,
        category: BindingError | None,
    ) -> L6BindingResult:
        return L6BindingResult(
            status=status,
            safe_error_category=category,
            route_identifier=L2_ROUTE_IDENTIFIER,
            engine_version=L2_LOCKED_ENGINE_VERSION,
            model_id=L2_LOCKED_MODEL_ID,
            future_output_format=L2_FUTURE_OUTPUT_FORMAT,
            output_handling_available=False,
            runtime_interaction_count=self._runtime_interaction_count,
        )


def exact_l6_probe() -> L6BindingProbe:
    return L6BindingProbe(
        probe_kind=L6_PROBE_KIND,
        probe_marker=L6_PROBE_MARKER,
        route_identifier=L2_ROUTE_IDENTIFIER,
        engine_version=L2_LOCKED_ENGINE_VERSION,
        model_id=L2_LOCKED_MODEL_ID,
        model_source_marker=L2_LOCKED_MODEL_SOURCE_MARKER,
        future_output_format=L2_FUTURE_OUTPUT_FORMAT,
    )

