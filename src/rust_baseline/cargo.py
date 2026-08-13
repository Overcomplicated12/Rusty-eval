"""Source acquisition and external-tool integration for Rust baseline scans."""

from __future__ import annotations

import json
import shutil
import subprocess
import tarfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import CrateSpec, ScanMode, ToolCommands, ToolRecord, ToolStatus
from .source_scan import _EXCLUDED_DIRS


class CargoError(RuntimeError):
    """Raised when source acquisition or package resolution fails."""


@dataclass(frozen=True)
class PackageResolution:
    """The selected package and production library target from Cargo metadata."""

    repository_root: Path
    workspace_root: Path
    package_root: Path
    manifest_path: Path
    package_name: str
    library_target_source: Path

    @property
    def production_source_roots(self) -> list[Path]:
        return [self.library_target_source.parent]


def run_command(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def tool_versions(tools: ToolCommands) -> dict[str, str | None]:
    return {
        "rustc": _version_output([tools.rustc, "--version"]),
        "cargo": _version_output([tools.cargo, "--version"]),
        "git": _version_output([tools.git, "--version"]),
    }


def checkout_crate(crate: CrateSpec, workspace_root: Path, tools: ToolCommands) -> Path:
    sources_root = workspace_root / "sources"
    sources_root.mkdir(parents=True, exist_ok=True)
    if crate.repo:
        return _checkout_git(crate, sources_root, tools)
    return _download_crates_io(crate, sources_root)


def find_package_manifest(checkout_root: Path, package: str) -> Path:
    matches: list[Path] = []
    for manifest in sorted(checkout_root.rglob("Cargo.toml")):
        relative_parts = manifest.relative_to(checkout_root).parts
        if any(part in _EXCLUDED_DIRS for part in relative_parts):
            continue
        try:
            import tomllib

            data = tomllib.loads(manifest.read_text(encoding="utf-8"))
        except Exception:
            continue
        package_table = data.get("package")
        if isinstance(package_table, dict) and package_table.get("name") == package:
            matches.append(manifest)
    if not matches:
        raise CargoError(f"could not find Cargo package '{package}' under {checkout_root}")
    if len(matches) > 1:
        raise CargoError(f"multiple Cargo manifests matched package '{package}' under {checkout_root}")
    return matches[0]


def resolve_package_library_target(checkout_root: Path, package: str, tools: ToolCommands) -> PackageResolution:
    """Resolve one package's library target without traversing sibling workspace packages."""
    result = run_command([tools.cargo, "metadata", "--format-version", "1", "--no-deps"], cwd=checkout_root)
    if result.returncode != 0:
        raise CargoError(f"cargo metadata failed for {package}: {result.stderr.strip()}")
    try:
        metadata = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise CargoError(f"cargo metadata produced invalid JSON for {package}") from error
    packages = [item for item in metadata.get("packages", []) if item.get("name") == package]
    if not packages:
        raise CargoError(f"cargo metadata could not find package '{package}'")
    if len(packages) > 1:
        raise CargoError(f"cargo metadata found multiple packages named '{package}'")
    selected = packages[0]
    library_targets = [target for target in selected.get("targets", []) if "lib" in target.get("kind", [])]
    if len(library_targets) != 1:
        raise CargoError(f"package '{package}' must expose exactly one library target")
    manifest_path = Path(selected["manifest_path"])
    library_target_source = Path(library_targets[0]["src_path"])
    package_root = manifest_path.parent
    if package_root not in library_target_source.parents:
        raise CargoError(f"library target for '{package}' is outside its package root")
    return PackageResolution(
        repository_root=checkout_root,
        workspace_root=Path(metadata["workspace_root"]),
        package_root=package_root,
        manifest_path=manifest_path,
        package_name=selected["name"],
        library_target_source=library_target_source,
    )


def probe_cargo_geiger(
    manifest_path: Path,
    mode: ScanMode,
    crate: CrateSpec,
    tools: ToolCommands,
    stdout_dir: Path,
) -> ToolRecord:
    help_command = [tools.cargo, "geiger", "--help"]
    cargo_path = shutil.which(tools.cargo)
    if cargo_path is None:
        return ToolRecord(tool="cargo-geiger", status=ToolStatus.TOOL_UNAVAILABLE, help_command=help_command)
    help_result = run_command(help_command, cwd=manifest_path.parent)
    if help_result.returncode != 0:
        return ToolRecord(
            tool="cargo-geiger",
            status=ToolStatus.TOOL_UNAVAILABLE,
            help_command=help_command,
            help_return_code=help_result.returncode,
            notes=["cargo geiger help failed", help_result.stderr.strip()],
        )
    version = _version_output([tools.cargo, "geiger", "--version"])
    plan = _machine_output_plan(help_result.stdout)
    if plan is None:
        return ToolRecord(
            tool="cargo-geiger",
            status=ToolStatus.MACHINE_OUTPUT_UNAVAILABLE,
            version=version,
            help_command=help_command,
            help_return_code=help_result.returncode,
            notes=["machine-readable output mode was not discovered from --help"],
        )
    command = [tools.cargo, "geiger"]
    if "--manifest-path" not in help_result.stdout:
        return ToolRecord(
            tool="cargo-geiger",
            status=ToolStatus.MACHINE_OUTPUT_UNAVAILABLE,
            version=version,
            help_command=help_command,
            help_return_code=help_result.returncode,
            notes=["--manifest-path support was not discoverable from --help"],
        )
    command.extend(["--manifest-path", str(manifest_path)])
    if mode is ScanMode.ALL_FEATURES and "--all-features" in help_result.stdout:
        command.append("--all-features")
    elif crate.features and "--features" in help_result.stdout:
        command.extend(["--features", ",".join(crate.features)])
    command.extend(plan)
    stdout_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = stdout_dir / "cargo-geiger.stdout.txt"
    stderr_path = stdout_dir / "cargo-geiger.stderr.txt"
    raw_path = stdout_dir.parent / "cargo_geiger_raw.json"
    result = run_command(command, cwd=manifest_path.parent)
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raw_path.write_text(json.dumps({"status": ToolStatus.FAILED.value, "stdout": result.stdout, "stderr": result.stderr}, indent=2) + "\n", encoding="utf-8")
        return ToolRecord(
            tool="cargo-geiger",
            status=ToolStatus.FAILED,
            version=version,
            machine_readable=True,
            command=command,
            return_code=result.returncode,
            help_command=help_command,
            help_return_code=help_result.returncode,
            raw_output_path=str(raw_path),
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            notes=["cargo-geiger execution failed"],
        )
    parsed = _safe_json(result.stdout)
    raw_path.write_text(json.dumps(parsed if parsed is not None else {"raw_stdout": result.stdout}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ToolRecord(
        tool="cargo-geiger",
        status=ToolStatus.OK,
        version=version,
        machine_readable=parsed is not None,
        command=command,
        return_code=result.returncode,
        help_command=help_command,
        help_return_code=help_result.returncode,
        raw_output_path=str(raw_path),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
    )


def probe_count_unsafe(root: Path, stdout_dir: Path) -> ToolRecord:
    command_name = shutil.which("count-unsafe")
    help_command = ["count-unsafe", "--help"]
    if command_name is None:
        return ToolRecord(tool="count-unsafe", status=ToolStatus.TOOL_UNAVAILABLE, help_command=help_command)
    help_result = run_command(help_command, cwd=root)
    if help_result.returncode != 0:
        return ToolRecord(
            tool="count-unsafe",
            status=ToolStatus.TOOL_UNAVAILABLE,
            help_command=help_command,
            help_return_code=help_result.returncode,
            notes=["count-unsafe help failed", help_result.stderr.strip()],
        )
    version = _version_output(["count-unsafe", "--version"])
    plan = _machine_output_plan(help_result.stdout)
    if plan is None:
        return ToolRecord(
            tool="count-unsafe",
            status=ToolStatus.MACHINE_OUTPUT_UNAVAILABLE,
            version=version,
            help_command=help_command,
            help_return_code=help_result.returncode,
            notes=["machine-readable output mode was not discovered from --help"],
        )
    command = ["count-unsafe", str(root)] + plan
    stdout_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = stdout_dir / "count-unsafe.stdout.txt"
    stderr_path = stdout_dir / "count-unsafe.stderr.txt"
    raw_path = stdout_dir.parent / "count_unsafe_raw.json"
    result = run_command(command, cwd=root)
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raw_path.write_text(json.dumps({"status": ToolStatus.FAILED.value, "stdout": result.stdout, "stderr": result.stderr}, indent=2) + "\n", encoding="utf-8")
        return ToolRecord(
            tool="count-unsafe",
            status=ToolStatus.FAILED,
            version=version,
            machine_readable=True,
            command=command,
            return_code=result.returncode,
            help_command=help_command,
            help_return_code=help_result.returncode,
            raw_output_path=str(raw_path),
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            notes=["count-unsafe execution failed"],
        )
    parsed = _safe_json(result.stdout)
    raw_path.write_text(json.dumps(parsed if parsed is not None else {"raw_stdout": result.stdout}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ToolRecord(
        tool="count-unsafe",
        status=ToolStatus.OK,
        version=version,
        machine_readable=parsed is not None,
        command=command,
        return_code=result.returncode,
        help_command=help_command,
        help_return_code=help_result.returncode,
        raw_output_path=str(raw_path),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
    )


def _checkout_git(crate: CrateSpec, sources_root: Path, tools: ToolCommands) -> Path:
    assert crate.repo and crate.rev
    destination = sources_root / f"{crate.name}-{crate.rev[:12]}"
    if destination.exists():
        return destination
    clone = run_command([tools.git, "clone", crate.repo, str(destination)])
    if clone.returncode != 0:
        raise CargoError(f"git clone failed for {crate.name}: {clone.stderr.strip()}")
    checkout = run_command([tools.git, "checkout", "--detach", crate.rev], cwd=destination)
    if checkout.returncode != 0:
        raise CargoError(f"git checkout failed for {crate.name}: {checkout.stderr.strip()}")
    return destination


def _download_crates_io(crate: CrateSpec, sources_root: Path) -> Path:
    assert crate.version
    destination = sources_root / f"{crate.name}-{crate.version}"
    if destination.exists():
        return destination
    archive = sources_root / f"{crate.name}-{crate.version}.crate"
    urllib.request.urlretrieve(crate.source_url, archive)
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as handle:
        handle.extractall(destination)
    extracted_root = destination / f"{crate.package}-{crate.version}"
    if extracted_root.exists():
        return extracted_root
    return destination


def _version_output(command: list[str]) -> str | None:
    binary = shutil.which(command[0])
    if binary is None:
        return None
    result = run_command(command)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or result.stderr.strip() or None


def _safe_json(value: str) -> dict[str, Any] | list[Any] | None:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _machine_output_plan(help_text: str) -> list[str] | None:
    lowered = help_text.lower()
    if "--output-format" in help_text and "json" in lowered:
        return ["--output-format", "json"]
    if "--format" in help_text and "json" in lowered:
        return ["--format", "json"]
    if "--json" in help_text:
        return ["--json"]
    return None
