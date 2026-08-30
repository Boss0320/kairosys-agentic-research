"""Default-deny local link validation for the curated case candidate."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET


_MARKDOWN_LINK = re.compile(r"(?<!\\)!?(?:\[[^\]]*\])\(([^)]+)\)")
_TEXT_SUFFIXES = frozenset({".md", ".html", ".svg"})
_DOCTYPE = re.compile(r"<!\s*DOCTYPE\b", re.IGNORECASE)


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    target: str
    reason: str


class LinkSourceError(ValueError):
    """A source document cannot be safely inspected for local links."""


class _HtmlLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value is not None:
                self.targets.append(value)


def _targets(path: Path) -> tuple[str, ...]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".md":
        return tuple(match.group(1).strip().strip("<>") for match in _MARKDOWN_LINK.finditer(text))
    if path.suffix == ".svg":
        if _DOCTYPE.search(text):
            raise LinkSourceError("doctype_not_allowed")
        try:
            root = ET.fromstring(text)
        except ET.ParseError as error:
            raise LinkSourceError("svg_parse_error") from error
        return tuple(
            value
            for node in root.iter()
            for name, value in node.attrib.items()
            if name.rsplit("}", 1)[-1] == "href"
        )
    parser = _HtmlLinks()
    parser.feed(text)
    return tuple(parser.targets)


def _validate(root: Path, source: Path, target: str) -> str | None:
    decoded_target = unquote(target)
    parsed = urlsplit(decoded_target)
    if decoded_target.startswith(("/", "~")) or parsed.scheme in {"file", "http", "https"}:
        return "absolute_or_external_target"
    if parsed.scheme or parsed.netloc:
        return "non_relative_target"
    location = parsed.path
    if not location:
        return None
    candidate = source.parent / location
    if candidate.is_symlink():
        return "symlink_target"
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(root)
    except ValueError:
        return "target_escapes_candidate"
    if not resolved_candidate.is_file():
        return "missing_target"
    return None


def check(root: Path) -> tuple[int, tuple[Finding, ...]]:
    if root.is_symlink() or not root.is_dir():
        return 0, (Finding(".", ".", "invalid_root"),)
    resolved_root = root.resolve()
    total = 0
    findings: list[Finding] = []
    for source in sorted(path for path in resolved_root.rglob("*") if path.is_file() and path.suffix in _TEXT_SUFFIXES):
        if source.is_symlink():
            findings.append(Finding(source.relative_to(resolved_root).as_posix(), ".", "symlink_source"))
            continue
        try:
            targets = _targets(source)
        except LinkSourceError as error:
            findings.append(Finding(source.relative_to(resolved_root).as_posix(), ".", str(error)))
            continue
        for target in targets:
            total += 1
            reason = _validate(resolved_root, source, target)
            if reason is not None:
                findings.append(Finding(source.relative_to(resolved_root).as_posix(), target, reason))
    return total, tuple(sorted(findings))


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(".")
    total, findings = check(root)
    print(f"Checked {total} links: {len(findings)} broken.")
    for finding in findings:
        print(f"{finding.path}: {finding.target} [{finding.reason}]")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
