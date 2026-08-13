"""Command-line access to reproducible Rust baseline scans."""

from __future__ import annotations

import argparse
import json

from .config import ConfigError
from .models import ScanMode
from .scanner import regenerate_report, run_scan, run_scan_all, validate_config


def _emit(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate-config")
    validate.add_argument("--config", required=True)

    scan = subcommands.add_parser("scan")
    scan.add_argument("--config", required=True)
    scan.add_argument("--crate", required=True)
    scan.add_argument("--mode", required=True, choices=[mode.value for mode in ScanMode])
    scan.add_argument("--experiment-id")

    scan_all = subcommands.add_parser("scan-all")
    scan_all.add_argument("--config", required=True)
    scan_all.add_argument("--mode", required=True, choices=[mode.value for mode in ScanMode])
    scan_all.add_argument("--experiment-id")

    report = subcommands.add_parser("report")
    report.add_argument("--results", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "validate-config":
            _emit(validate_config(args.config))
        elif args.command == "scan":
            path = run_scan(args.config, args.crate, ScanMode(args.mode), args.experiment_id)
            _emit({"results": str(path)})
        elif args.command == "scan-all":
            path = run_scan_all(args.config, ScanMode(args.mode), args.experiment_id)
            _emit({"results": str(path)})
        else:
            path = regenerate_report(args.results)
            _emit({"results": str(path)})
    except ConfigError as error:
        parser.error(str(error))
    except Exception as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
