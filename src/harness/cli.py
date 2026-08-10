"""Command-line access to validation and non-mutating Phase 2 dry runs."""

from __future__ import annotations

import argparse
import json

from .config import ConfigError, load_config
from .experiment import ExperimentController
from .selection import SelectionError, find_unit, load_selection


def _emit(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate-config", "show-config"):
        command = subcommands.add_parser(name)
        command.add_argument("--config", required=True)
    dry_run = subcommands.add_parser("dry-run")
    dry_run.add_argument("--config", required=True)
    dry_run.add_argument("--selection", required=True)
    dry_run.add_argument("--unit", default=None)
    show_unit = subcommands.add_parser("show-unit")
    show_unit.add_argument("--selection", required=True)
    show_unit.add_argument("--unit", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command in ("validate-config", "show-config"):
            config = load_config(args.config)
            if args.command == "show-config":
                _emit(config.to_dict())
            else:
                print("configuration is valid")
        elif args.command == "show-unit":
            _emit(find_unit(args.selection, args.unit).to_dict())
        else:
            config = load_config(args.config)
            unit = find_unit(args.selection, args.unit) if args.unit else load_selection(args.selection)[0]
            _emit(ExperimentController(config, unit).dry_run())
    except (ConfigError, SelectionError, IndexError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
