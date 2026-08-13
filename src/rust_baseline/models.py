"""JSON-serializable records for reproducible Rust baseline scans."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from . import RUST_BASELINE_SCHEMA_VERSION, RUST_BASELINE_SCANNER_VERSION


class SourceKind(StrEnum):
    GIT = "git"
    CRATES_IO = "crates.io"


class ScanMode(StrEnum):
    DEFAULT = "default"
    ALL_FEATURES = "all-features"


class ToolStatus(StrEnum):
    OK = "OK"
    TOOL_UNAVAILABLE = "TOOL_UNAVAILABLE"
    MACHINE_OUTPUT_UNAVAILABLE = "MACHINE_OUTPUT_UNAVAILABLE"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ScanStatus(StrEnum):
    OK = "OK"
    FAILED = "FAILED"


class SourceScanStatus(StrEnum):
    OK = "OK"
    FAILED = "FAILED"


class UnsafeCategory(StrEnum):
    RAW_POINTER = "raw_pointer"
    FFI_SYSCALL = "ffi_syscall"
    ALLOCATION_LAYOUT = "allocation_layout"
    ATOMICS_CONCURRENCY = "atomics_concurrency"
    SIMD_INTRINSICS = "simd_intrinsics"
    BUFFER_ZERO_COPY = "buffer_zero_copy"
    PINNING_LIFETIME = "pinning_lifetime"
    OTHER = "other"


class JsonRecord:
    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


def _json_value(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class ToolCommands(JsonRecord):
    cargo: str = "cargo"
    git: str = "git"
    rustc: str = "rustc"


@dataclass(frozen=True)
class CrateSpec(JsonRecord):
    name: str
    package: str
    repo: str | None = None
    rev: str | None = None
    version: str | None = None
    features: list[str] = field(default_factory=list)

    @property
    def source_kind(self) -> SourceKind:
        if self.repo:
            return SourceKind.GIT
        return SourceKind.CRATES_IO

    @property
    def source_url(self) -> str:
        if self.repo:
            return self.repo
        return f"https://crates.io/api/v1/crates/{self.package}/{self.version}/download"

    @property
    def pinned_reference(self) -> str:
        return self.rev or self.version or ""


@dataclass(frozen=True)
class BaselineConfig(JsonRecord):
    workspace_root: Path
    results_root: Path
    crates: list[CrateSpec]
    tools: ToolCommands = field(default_factory=ToolCommands)


@dataclass(frozen=True)
class UnsafeCategoryAnnotation(JsonRecord):
    category: UnsafeCategory
    file: str
    line_start: int
    line_end: int
    notes: str = ""


@dataclass(frozen=True)
class FileSummary(JsonRecord):
    path: str
    physical_loc: int
    nonblank_loc: int
    functions_total: int
    functions_safe: int
    functions_unsafe_declared: int
    functions_with_unsafe: int
    functions_unsafe_any: int
    functions_with_any_explicit_unsafe: int
    functions_without_explicit_unsafe: int
    unsafe_traits: int
    unsafe_impls: int
    unsafe_blocks: int
    unsafe_loc_estimate: int
    unsafe_lines_estimate: list[int]


@dataclass(frozen=True)
class SourceMetrics(JsonRecord):
    production_files: int
    physical_loc: int
    nonblank_loc: int
    functions_total: int
    functions_safe: int
    functions_unsafe_declared: int
    functions_with_unsafe: int
    functions_unsafe_any: int
    functions_with_any_explicit_unsafe: int
    functions_without_explicit_unsafe: int
    safe_function_pct: float | None
    functions_without_explicit_unsafe_pct: float | None
    unsafe_fn_count: int
    unsafe_trait_count: int
    unsafe_impl_count: int
    unsafe_block_count: int
    unsafe_loc_estimate: int
    unsafe_loc_pct_estimate: float | None
    files_with_unsafe: int
    unsafe_file_pct: float | None
    top5_unsafe_block_concentration_pct: float | None
    top5_unsafe_loc_concentration_pct_estimate: float | None


@dataclass(frozen=True)
class ToolRecord(JsonRecord):
    tool: str
    status: ToolStatus
    version: str | None = None
    machine_readable: bool = False
    command: list[str] = field(default_factory=list)
    return_code: int | None = None
    help_command: list[str] = field(default_factory=list)
    help_return_code: int | None = None
    notes: list[str] = field(default_factory=list)
    raw_output_path: str | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None


@dataclass(frozen=True)
class CheckoutMetadata(JsonRecord):
    source_kind: SourceKind
    source_url: str
    pinned_reference: str
    checkout_root: str
    repository_root: str
    workspace_root: str
    package_root: str
    manifest_path: str
    package_name: str
    library_target_source: str
    production_source_roots: list[str]


@dataclass(frozen=True)
class BaselineResult(JsonRecord):
    schema_version: str = RUST_BASELINE_SCHEMA_VERSION
    scanner_version: str = RUST_BASELINE_SCANNER_VERSION
    experiment_id: str = ""
    crate_name: str = ""
    package: str = ""
    revision: str = ""
    mode: ScanMode = ScanMode.DEFAULT
    scan_date: str = ""
    enabled_features: list[str] = field(default_factory=list)
    default_features_enabled: bool = True
    all_features_enabled: bool = False
    source_checkout: CheckoutMetadata | None = None
    rust_toolchain: dict[str, str | None] = field(default_factory=dict)
    source_scan_status: SourceScanStatus = SourceScanStatus.OK
    scan_status: ScanStatus = ScanStatus.OK
    summary: dict[str, Any] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)
    unsafe_category_annotations: list[UnsafeCategoryAnnotation] = field(default_factory=list)
