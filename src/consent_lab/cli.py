"""Command line for the offline measurement and the credit-gated probe."""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from consent_lab import __version__
from consent_lab.config import Settings
from consent_lab.errors import ConfigError, ConsentLabError
from consent_lab.logging_setup import add_redaction, configure


def _show(path: Path) -> str:
    if path.is_absolute():
        try:
            return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            return path.name
    return path.as_posix()


def _load_settings(env: Mapping[str, str] | None) -> Settings | None:
    try:
        return Settings.from_env(env)
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return None


def cmd_about(settings: Settings) -> int:
    print(f"consent_lab {__version__}")
    print(f"live_enabled={str(settings.live_enabled).lower()}")
    print("offline: python -m consent_lab measure")
    print("live probe: off unless LIVE_ENABLED=1 (spends credits)")
    return 0


def cmd_measure(settings: Settings, root: str | None, out: str | None) -> int:
    from consent_lab.measure import display_path, format_line, measure_tree, write_csv

    evidence = Path(root) if root else Path(settings.evidence_root)
    dest = Path(out) if out else evidence / "measurements.csv"
    try:
        rows = measure_tree(
            evidence,
            sample_rate=settings.sample_rate,
            min_samples=settings.min_samples,
        )
    except ConsentLabError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not rows:
        print("no voiced turns", file=sys.stderr)
        return 2
    write_csv(rows, dest)
    for row in rows:
        print(format_line(row))
    print(f"wrote {display_path(dest)} ({len(rows)} rows)")
    return 0


def cmd_probe(settings: Settings, out: str | None) -> int:
    from consent_lab.probe import run_probe

    message = settings.refusal_message(out)
    if message or out is None:
        print(
            message or "need ELEVENLABS_API_KEY, ELEVENLABS_AGENT_ID and an output dir",
            file=sys.stderr,
        )
        return 2
    add_redaction(settings.api_key)
    try:
        durs = asyncio.run(run_probe(settings=settings, out_dir=Path(out)))
    except ConsentLabError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(_show(Path(out)), [round(item, 2) for item in durs])
    return 0


def cmd_secretscan(paths: Sequence[str]) -> int:
    from consent_lab.secretscan import main as scan_main

    return scan_main(paths)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="consent_lab")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("about", help="print version and whether the live probe is enabled")
    measure = sub.add_parser("measure", help="recompute F0 and centroid for an evidence directory")
    measure.add_argument("--root", default=None)
    measure.add_argument("--out", default=None)
    probe = sub.add_parser("probe", help="record a scripted call (spends credits)")
    probe.add_argument("out", nargs="?")
    scan = sub.add_parser("secretscan", help="scan files for key shapes and local absolute paths")
    scan.add_argument("paths", nargs="*")
    return parser


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    settings = _load_settings(env)
    if settings is None:
        return 2
    configure(settings.log_level)
    if args.cmd == "about":
        return cmd_about(settings)
    if args.cmd == "measure":
        return cmd_measure(settings, args.root, args.out)
    if args.cmd == "probe":
        return cmd_probe(settings, args.out)
    return cmd_secretscan(args.paths)


def console_main() -> None:
    raise SystemExit(main())
