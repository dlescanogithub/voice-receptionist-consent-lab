"""Scan text files for key shapes and local absolute paths.

The finding id is printed. The matching line is not, so a hit does not copy
the secret into the log.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

# Built without a contiguous absolute path, so this file does not contain one.
_HOME = "/" + "home" + "/"
_WORKSPACE = "/" + "workspace" + "/"

_SKIP_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "htmlcov",
        ".eggs",
    }
)
_BINARY = frozenset(
    {".wav", ".mp3", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pyc", ".so", ".whl"}
)

_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("aws_access_key_id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("elevenlabs_secret_key", re.compile(r"\bsk_[A-Za-z0-9]{32,}\b")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    (
        "assigned_live_secret",
        re.compile(
            r"(?i)\b(?:api_key|apikey|api_token|secret|password)\b\s*[:=]\s*['\"][^'\"]{12,}['\"]"
        ),
    ),
    ("home_path", re.compile(re.escape(_HOME))),
    ("workspace_path", re.compile(re.escape(_WORKSPACE))),
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str


def iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in _BINARY:
            continue
        yield path


def scan_text(relative: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in _RULES:
            if pattern.search(line):
                findings.append(Finding(path=relative, line=number, rule=rule))
    return findings


def scan_path(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    base = root if root.is_dir() else root.parent
    for path in iter_files(root):
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"\x00" in data[:1024]:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        try:
            relative = path.resolve().relative_to(base.resolve()).as_posix()
        except ValueError:
            relative = path.name
        findings.extend(scan_text(relative, text))
    return findings


def format_report(findings: Sequence[Finding]) -> str:
    if not findings:
        return "secret scan: no findings"
    lines = ["secret scan: findings"]
    lines.extend(f"{item.path}:{item.line}: {item.rule}" for item in findings)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    roots = [Path(arg) for arg in args] if args else [Path(".")]
    findings: list[Finding] = []
    for root in roots:
        findings.extend(scan_path(root))
    print(format_report(findings))
    return 1 if findings else 0
