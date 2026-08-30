"""Deterministically reject content that cannot enter the clean-room candidate."""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    rule: str
    excerpt: str


_ALLOWED_SUFFIXES = frozenset(
    {".css", ".html", ".js", ".json", ".md", ".py", ".svg", ".toml", ".txt"}
)
_ALLOWED_EXTENSIONLESS = frozenset({".gitignore", "PUBLIC-MANIFEST.txt", "LICENSE"})
_RUNTIME_CACHE_NAMES = frozenset({"__pycache__", ".pytest_cache", ".ruff_cache"})
_PROVIDER_NAMES = tuple(
    "".join(parts)
    for parts in (
        ("Open", "AI"),
        ("Pine", "cone"),
        ("Fin", "Mind"),
        ("Alpha ", "Vantage"),
        ("y", "finance"),
        ("Sup", "abase"),
        ("Poly", "gon"),
        ("I", "EX"),
    )
)
_SECRET_NAME = re.compile(
    r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*_(?:KEY|TOKEN|PASSWORD|SECRET)\b",
    re.IGNORECASE,
)
_PRIVATE_KEY = re.compile(r"-----BEGIN " r"(?:[A-Z ]*)" r"PRIVATE KEY-----")
_RULES = (
    ("internal_label", re.compile(r"\bK_" r"ReAct\b")),
    ("private_path", re.compile(r"(?<!\w)/" r"(?:Users|home)/")),
    (
        "secret_assignment",
        re.compile(_SECRET_NAME.pattern + r"\s*[:=]\s*\S+", re.IGNORECASE),
    ),
    ("private_key", _PRIVATE_KEY),
    (
        "current_live_claim",
        re.compile(r"\bKairosys\s+is\s+(?:currently\s+)?live\b", re.IGNORECASE),
    ),
    ("production_claim", re.compile(r"\bproduction" r"[-\s]" r"ready\b", re.IGNORECASE)),
    ("performance_claim", re.compile(r"\bguaranteed\s+" r"alpha\b", re.IGNORECASE)),
    ("absolute_claim", re.compile(r"\bcatches\s+every\s+error\b", re.IGNORECASE)),
    (
        "provider_name",
        re.compile(r"\b(?:" + "|".join(map(re.escape, _PROVIDER_NAMES)) + r")\b", re.IGNORECASE),
    ),
    (
        "ticker_symbol",
        re.compile(
            r"\b(?:NYSE|NASDAQ|TWSE|TPEX)\s*:\s*[A-Z]{1,5}\b"
            r"|\b\d{4}\.(?:TW|TWO)\b"
            r"|(?<!\w)\$[A-Z]{1,5}\b"
        ),
    ),
)


def _relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _path_finding(root: Path, path: Path) -> Finding | None:
    name = path.name
    relative_path = _relative_path(root, path)
    if name.startswith(".env"):
        return Finding(relative_path, 0, "dotenv_file", "<redacted environment file>")
    if name == ".git":
        return Finding(relative_path, 0, "git_metadata", "<git metadata>")
    if path.suffix not in _ALLOWED_SUFFIXES and name not in _ALLOWED_EXTENSIONLESS:
        return Finding(relative_path, 0, "unsupported_file_type", "<unsupported file type>")
    return None


def _excerpt(line: str) -> str:
    if _SECRET_NAME.search(line) or _PRIVATE_KEY.search(line):
        return "<redacted suspected secret>"
    return line.strip()[:160]


def _scan_file(root: Path, path: Path) -> tuple[Finding, ...]:
    path_finding = _path_finding(root, path)
    if path_finding is not None:
        return (path_finding,)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return (Finding(_relative_path(root, path), 0, "invalid_utf8", "<non-UTF-8 text>"),)

    findings = []
    relative_path = _relative_path(root, path)
    for line_number, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in _RULES:
            if pattern.search(line):
                findings.append(Finding(relative_path, line_number, rule, _excerpt(line)))
    return tuple(findings)


def scan_tree(root: Path) -> tuple[Finding, ...]:
    """Return stable, redacted findings for prohibited public content."""
    supplied_root = root.as_posix()
    if root.is_symlink():
        return (Finding(supplied_root, 0, "symlink", "<symlink root>"),)
    if not root.is_dir():
        return (Finding(supplied_root, 0, "invalid_root", "<invalid scan root>"),)
    resolved_root = root.resolve()
    findings = []
    for directory, directory_names, file_names in os.walk(resolved_root, followlinks=False):
        current = Path(directory)
        directory_names.sort()
        file_names.sort()
        retained_directories = []
        for name in directory_names:
            candidate = current / name
            if candidate.is_symlink():
                findings.append(Finding(_relative_path(resolved_root, candidate), 0, "symlink", "<symlink>"))
            elif name in _RUNTIME_CACHE_NAMES:
                findings.append(
                    Finding(_relative_path(resolved_root, candidate), 0, "runtime_cache", "<runtime cache>")
                )
            elif name == ".git":
                findings.append(
                    Finding(_relative_path(resolved_root, candidate), 0, "git_metadata", "<git metadata>")
                )
            else:
                retained_directories.append(name)
        directory_names[:] = retained_directories
        for name in file_names:
            candidate = current / name
            if candidate.is_symlink():
                findings.append(Finding(_relative_path(resolved_root, candidate), 0, "symlink", "<symlink>"))
            else:
                findings.extend(_scan_file(resolved_root, candidate))
    return tuple(sorted(findings))


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(".")
    findings = scan_tree(root)
    print(json.dumps([asdict(finding) for finding in findings], indent=2))
    if findings and findings[0].rule == "invalid_root":
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
