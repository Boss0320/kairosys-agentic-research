"""Assemble an exact clean-room candidate from a sorted public manifest."""

from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET


_TEXT_SUFFIXES = frozenset(
    {".css", ".html", ".js", ".json", ".md", ".py", ".toml", ".txt"}
)
_APPROVED_EXTENSIONLESS = frozenset({".gitignore", "LICENSE"})
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")
_DOCTYPE = re.compile(br"<!\s*DOCTYPE\b", re.IGNORECASE)


class AssemblyError(ValueError):
    """The requested assembly is ambiguous or outside the public contract."""


def _absolute_without_resolving(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _manifest_path(source: Path, supplied: Path) -> tuple[Path, str]:
    candidate = supplied if supplied.is_absolute() else source / supplied
    candidate = _absolute_without_resolving(candidate)
    if candidate.is_symlink():
        raise AssemblyError("manifest must be a regular non-symlink file")
    resolved_candidate = candidate.resolve(strict=False)
    try:
        relative = resolved_candidate.relative_to(source)
    except ValueError as error:
        raise AssemblyError("manifest must be inside source") from error
    relative_name = relative.as_posix()
    if not relative_name or relative_name == ".":
        raise AssemblyError("manifest must be a named file inside source")
    _reject_symlink_components(source, relative)
    if not resolved_candidate.is_file():
        raise AssemblyError("manifest must be a regular non-symlink file")
    return resolved_candidate, relative_name


def _reject_symlink_components(source: Path, relative: Path) -> None:
    current = source
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise AssemblyError(f"manifested path contains a symlink: {relative.as_posix()}")


def _validate_relative_entry(entry: str) -> PurePosixPath:
    if entry != entry.strip():
        raise AssemblyError("manifest entries must not contain surrounding whitespace")
    if "\\" in entry or entry.startswith("/") or _WINDOWS_DRIVE.match(entry):
        raise AssemblyError(f"manifest path must be relative POSIX: {entry!r}")
    raw_parts = entry.split("/")
    if not entry or any(part == "" for part in raw_parts):
        raise AssemblyError("manifest contains an empty path component")
    if any(part == "." for part in raw_parts):
        raise AssemblyError("manifest contains a current-directory component")
    if any(part == ".." for part in raw_parts):
        raise AssemblyError("manifest contains parent traversal")
    if any(any(ord(character) < 32 for character in part) for part in raw_parts):
        raise AssemblyError("manifest path contains a control character")
    normalized = unicodedata.normalize("NFC", entry)
    if normalized != entry:
        raise AssemblyError("manifest paths must use NFC normalization")
    return PurePosixPath(*raw_parts)


def _read_manifest(path: Path, own_name: str) -> tuple[PurePosixPath, ...]:
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as error:
        raise AssemblyError("manifest must be UTF-8") from error
    if not text or not text.endswith("\n") or "\r" in text:
        raise AssemblyError("manifest must be non-empty LF-terminated UTF-8 text")
    lines = text[:-1].split("\n")
    if any(line == "" for line in lines):
        raise AssemblyError("manifest contains a blank entry")
    if len(lines) != len(set(lines)):
        raise AssemblyError("manifest contains a duplicate path")
    folded = [unicodedata.normalize("NFC", line).casefold() for line in lines]
    if len(folded) != len(set(folded)):
        raise AssemblyError("manifest contains case-ambiguous paths")
    if lines != sorted(lines):
        raise AssemblyError("manifest must be sorted")
    entries = tuple(_validate_relative_entry(line) for line in lines)
    if own_name not in lines:
        raise AssemblyError("manifest must list itself")
    return entries


def _validate_type(path: Path, data: bytes) -> None:
    if path.suffix == ".svg":
        if _DOCTYPE.search(data):
            raise AssemblyError(f"manifested SVG is not approved: {path.as_posix()}")
        try:
            text = data.decode("utf-8")
            root = ET.fromstring(text)
        except (UnicodeDecodeError, ET.ParseError) as error:
            raise AssemblyError(f"manifested file is not an approved SVG: {path.as_posix()}") from error
        if root.tag.rsplit("}", 1)[-1] != "svg":
            raise AssemblyError(f"manifested file is not an approved SVG: {path.as_posix()}")
        return
    if path.suffix not in _TEXT_SUFFIXES and path.name not in _APPROVED_EXTENSIONLESS:
        raise AssemblyError(f"unsupported public file type: {path.as_posix()}")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AssemblyError(f"manifested text must be UTF-8: {path.as_posix()}") from error


def _source_bytes(source: Path, entry: PurePosixPath) -> bytes:
    relative = Path(*entry.parts)
    _reject_symlink_components(source, relative)
    candidate = source.joinpath(*entry.parts)
    if candidate.is_symlink() or not candidate.is_file():
        raise AssemblyError(f"manifested path is a missing regular file: {entry.as_posix()}")
    try:
        candidate.resolve(strict=True).relative_to(source)
    except (FileNotFoundError, ValueError) as error:
        raise AssemblyError(f"manifested path escapes source: {entry.as_posix()}") from error
    data = candidate.read_bytes()
    _validate_type(candidate, data)
    return data


def _prepare_destination(source: Path, destination: Path) -> Path:
    supplied = _absolute_without_resolving(destination)
    if supplied.is_symlink():
        raise AssemblyError("destination must not be a symlink")
    resolved = supplied.resolve(strict=False)
    try:
        resolved.relative_to(source)
    except ValueError:
        pass
    else:
        raise AssemblyError("destination must not be inside source")
    if supplied.exists():
        if not supplied.is_dir():
            raise AssemblyError("destination must be a directory")
        if any(supplied.iterdir()):
            raise AssemblyError("destination is not empty")
    return supplied


def assemble(source: Path, destination: Path, manifest: Path) -> tuple[Path, ...]:
    """Copy only regular UTF-8 or approved SVG files named by the manifest."""
    supplied_source = Path(source)
    if supplied_source.is_symlink() or not supplied_source.is_dir():
        raise AssemblyError("source must be a regular non-symlink directory")
    source_root = supplied_source.resolve(strict=True)
    manifest_path, own_name = _manifest_path(source_root, Path(manifest))
    destination_root = _prepare_destination(source_root, Path(destination))
    entries = _read_manifest(manifest_path, own_name)

    payloads = tuple(
        (entry, _source_bytes(source_root, entry))
        for entry in entries
    )
    destination_root.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for entry, data in payloads:
        target = destination_root.joinpath(*entry.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        copied.append(target)

    actual = tuple(
        path.relative_to(destination_root).as_posix()
        for path in sorted(destination_root.rglob("*"))
        if path.is_file()
    )
    expected = tuple(entry.as_posix() for entry in entries)
    if actual != expected:
        raise AssemblyError("assembled destination does not exactly match manifest")
    return tuple(copied)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    arguments = parser.parse_args(argv)
    try:
        copied = assemble(arguments.source, arguments.destination, arguments.manifest)
    except (AssemblyError, OSError) as error:
        print(f"Assembly rejected: {error}", file=sys.stderr)
        return 2
    print(f"Assembled {len(copied)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
