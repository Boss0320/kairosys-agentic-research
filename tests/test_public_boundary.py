from __future__ import annotations

import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts.assemble_public import AssemblyError, assemble
from scripts.check_public_boundary import Finding, main, scan_tree


APPROVED_RIGHTS_NOTICE = """Copyright (c) 2026 Titus Lai. All rights reserved.

This repository is published for portfolio review and evaluation only. You may
view, clone, and run it locally to evaluate the author's work. No permission is
granted to reuse, modify, redistribute, or incorporate any part of this
repository into other software, products, services, or publications, commercial
or otherwise, without prior written permission from the author.
"""


class PublicBoundaryScannerTests(unittest.TestCase):
    def scan_text(self, text: str) -> tuple:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "candidate.md").write_text(text, encoding="utf-8")
            return scan_tree(root)

    def scan_file(self, name: str, content: str = "safe text") -> tuple:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / name).write_text(content, encoding="utf-8")
            return scan_tree(root)

    def test_rejects_internal_product_label(self) -> None:
        findings = self.scan_text("The current repo is " + "K_" + "ReAct")
        self.assertEqual({item.rule for item in findings}, {"internal_label"})

    def test_rejects_absolute_private_path(self) -> None:
        findings = self.scan_text("/" + "Users/example/Desktop/project")
        self.assertEqual({item.rule for item in findings}, {"private_path"})

    def test_rejects_secret_assignment_without_echoing_value(self) -> None:
        findings = self.scan_text("API" + "_KEY='synthetic-secret'")
        self.assertEqual({item.rule for item in findings}, {"secret_assignment"})
        self.assertNotIn("synthetic-secret", " ".join(item.excerpt for item in findings))

    def test_rejects_vendor_prefixed_secret_assignments_without_echoing_value(self) -> None:
        for name in (
            "OPEN" + "AI_API_KEY",
            "PINE" + "CONE_API_KEY",
            "AWS" + "_SECRET_ACCESS_KEY",
            "GITHUB" + "_TOKEN",
        ):
            with self.subTest(name=name):
                findings = self.scan_text(name + "='synthetic-secret'")
                self.assertEqual({item.rule for item in findings}, {"secret_assignment"})
                self.assertNotIn("synthetic-secret", " ".join(item.excerpt for item in findings))

    def test_rejects_terminal_secret_assignments_without_echoing_value(self) -> None:
        for name in ("DATABASE" + "_SECRET", "OPEN" + "AI_SECRET"):
            with self.subTest(name=name):
                findings = self.scan_text(name + "='synthetic-secret'")
                self.assertEqual({item.rule for item in findings}, {"secret_assignment"})
                self.assertNotIn("synthetic-secret", " ".join(item.excerpt for item in findings))

    def test_rejects_current_live_claim(self) -> None:
        findings = self.scan_text("Kairosys is currently " + "live.")
        self.assertEqual({item.rule for item in findings}, {"current_live_claim"})

    def test_rejects_runtime_cache_and_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "__pycache__").mkdir()
            target = root / "safe.md"
            target.write_text("synthetic", encoding="utf-8")
            os.symlink(target, root / "linked.md")
            findings = scan_tree(root)
        self.assertEqual({item.rule for item in findings}, {"runtime_cache", "symlink"})

    def test_rejects_each_runtime_cache_directory(self) -> None:
        for name in ("__pycache__", ".pytest_cache", ".ruff_cache"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                (root / name).mkdir()
                findings = scan_tree(root)
                self.assertEqual({item.rule for item in findings}, {"runtime_cache"})

    def test_rejects_symlink_scan_root_before_resolving(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "candidate"
            target.mkdir()
            symlink_root = root / "candidate-link"
            os.symlink(target, symlink_root)
            self.assertEqual(
                scan_tree(symlink_root),
                (Finding(symlink_root.as_posix(), 0, "symlink", "<symlink root>"),),
            )

    def test_invalid_roots_return_deterministic_finding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            missing = root / "missing-root"
            file_root = root / "not-a-directory.md"
            file_root.write_text("synthetic", encoding="utf-8")
            for invalid_root in (missing, file_root):
                with self.subTest(root=invalid_root):
                    self.assertEqual(
                        scan_tree(invalid_root),
                        (Finding(invalid_root.as_posix(), 0, "invalid_root", "<invalid scan root>"),),
                    )

    def test_cli_returns_two_for_invalid_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing = Path(temporary_directory) / "missing-root"
            output = StringIO()
            with patch("scripts.check_public_boundary.sys.argv", ["scanner", str(missing)]):
                with redirect_stdout(output):
                    exit_code = main()
        self.assertEqual(exit_code, 2)
        self.assertIn('"rule": "invalid_root"', output.getvalue())

    def test_rejects_dotenv_file(self) -> None:
        findings = self.scan_file(".env" + ".local")
        self.assertEqual({item.rule for item in findings}, {"dotenv_file"})

    def test_rejects_private_key_marker(self) -> None:
        findings = self.scan_text("-----BEGIN " + "PRIVATE KEY-----")
        self.assertEqual({item.rule for item in findings}, {"private_key"})

    def test_rejects_overclaims(self) -> None:
        for text, expected_rule in (
            ("This is " + "production-" + "ready.", "production_claim"),
            ("It provides " + "guaranteed " + "alpha.", "performance_claim"),
            ("It " + "catches " + "every error.", "absolute_claim"),
        ):
            with self.subTest(text=text):
                findings = self.scan_text(text)
                self.assertEqual({item.rule for item in findings}, {expected_rule})

    def test_rejects_provider_name(self) -> None:
        findings = self.scan_text("Open" + "AI")
        self.assertEqual({item.rule for item in findings}, {"provider_name"})

    def test_rejects_real_ticker_notation(self) -> None:
        findings = self.scan_text("NASDAQ" + ": AAPL")
        self.assertEqual({item.rule for item in findings}, {"ticker_symbol"})

    def test_rejects_unknown_binary_type(self) -> None:
        findings = self.scan_file("payload.bin")
        self.assertEqual({item.rule for item in findings}, {"unsupported_file_type"})

    def test_rejects_non_utf8_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "invalid.md").write_bytes(bytes((255, 254)))
            findings = scan_tree(root)
        self.assertEqual({item.rule for item in findings}, {"invalid_utf8"})

    def test_allows_approved_synthetic_language(self) -> None:
        findings = self.scan_text(
            "SYNTH-KAI-01 is a synthetic editable analyst draft from April 2025."
        )
        self.assertEqual(findings, ())

    def test_allows_extensionless_public_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for name in (".gitignore", "PUBLIC-MANIFEST.txt", "LICENSE"):
                (root / name).write_text("synthetic", encoding="utf-8")
            self.assertEqual(scan_tree(root), ())


class PublicAssemblyTests(unittest.TestCase):
    def write_manifest(self, source: Path, entries: tuple[str, ...]) -> Path:
        manifest = source / "PUBLIC-MANIFEST.txt"
        manifest.write_text("\n".join(entries) + "\n", encoding="utf-8")
        return manifest

    def test_current_candidate_has_approved_rights_notice_in_exact_49_file_manifest(self) -> None:
        root = Path(__file__).resolve().parents[1]
        license_path = root / "LICENSE"
        self.assertTrue(license_path.is_file(), "approved rights notice must ship as LICENSE")
        self.assertEqual(license_path.read_text(encoding="utf-8"), APPROVED_RIGHTS_NOTICE)

        entries = tuple((root / "PUBLIC-MANIFEST.txt").read_text(encoding="utf-8").splitlines())
        self.assertEqual(len(entries), 49)
        self.assertEqual(entries, tuple(sorted(entries)))
        self.assertIn("LICENSE", entries)

    def test_copies_exact_manifest_and_ignores_undeclared_source_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()
            destination.mkdir()
            (source / "assets").mkdir()
            (source / "assets" / "diagram.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"><title>Diagram</title></svg>',
                encoding="utf-8",
            )
            (source / "safe.txt").write_text("safe\n", encoding="utf-8")
            (source / "private-notes.txt").write_text("do not copy\n", encoding="utf-8")
            manifest = self.write_manifest(
                source,
                ("PUBLIC-MANIFEST.txt", "assets/diagram.svg", "safe.txt"),
            )

            copied = assemble(source, destination, manifest)

            self.assertEqual(
                tuple(path.relative_to(destination).as_posix() for path in copied),
                ("PUBLIC-MANIFEST.txt", "assets/diagram.svg", "safe.txt"),
            )
            self.assertEqual(
                tuple(
                    path.relative_to(destination).as_posix()
                    for path in sorted(destination.rglob("*"))
                    if path.is_file()
                ),
                ("PUBLIC-MANIFEST.txt", "assets/diagram.svg", "safe.txt"),
            )
            self.assertFalse((destination / "private-notes.txt").exists())
            self.assertEqual((destination / "safe.txt").read_text(encoding="utf-8"), "safe\n")

    def test_rejects_duplicate_manifest_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            manifest = self.write_manifest(
                source,
                ("PUBLIC-MANIFEST.txt", "PUBLIC-MANIFEST.txt"),
            )
            with self.assertRaisesRegex(AssemblyError, "duplicate"):
                assemble(source, root / "destination", manifest)

    def test_rejects_absolute_manifest_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            manifest = self.write_manifest(
                source,
                ("/private/tmp/escape.txt", "PUBLIC-MANIFEST.txt"),
            )
            with self.assertRaisesRegex(AssemblyError, "relative"):
                assemble(source, root / "destination", manifest)

    def test_rejects_parent_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            manifest = self.write_manifest(source, ("../escape.txt", "PUBLIC-MANIFEST.txt"))
            with self.assertRaisesRegex(AssemblyError, "parent traversal"):
                assemble(source, root / "destination", manifest)

    def test_rejects_symlinked_manifest_file_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            target = source / "target.txt"
            target.write_text("safe\n", encoding="utf-8")
            os.symlink(target, source / "linked.txt")
            manifest = self.write_manifest(
                source,
                ("PUBLIC-MANIFEST.txt", "linked.txt"),
            )
            with self.assertRaisesRegex(AssemblyError, "symlink"):
                assemble(source, root / "destination", manifest)

    def test_rejects_symlinked_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            target = root / "outside"
            target.mkdir()
            (target / "safe.txt").write_text("safe\n", encoding="utf-8")
            os.symlink(target, source / "linked")
            manifest = self.write_manifest(
                source,
                ("PUBLIC-MANIFEST.txt", "linked/safe.txt"),
            )
            with self.assertRaisesRegex(AssemblyError, "symlink"):
                assemble(source, root / "destination", manifest)

    def test_rejects_missing_manifest_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            manifest = self.write_manifest(
                source,
                ("PUBLIC-MANIFEST.txt", "missing.txt"),
            )
            with self.assertRaisesRegex(AssemblyError, "missing regular file"):
                assemble(source, root / "destination", manifest)

    def test_rejects_destination_residue_before_copying(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()
            destination.mkdir()
            (source / "safe.txt").write_text("safe\n", encoding="utf-8")
            (destination / "residue.txt").write_text("residue\n", encoding="utf-8")
            manifest = self.write_manifest(
                source,
                ("PUBLIC-MANIFEST.txt", "safe.txt"),
            )
            with self.assertRaisesRegex(AssemblyError, "destination is not empty"):
                assemble(source, destination, manifest)
            self.assertEqual((destination / "residue.txt").read_text(encoding="utf-8"), "residue\n")

    def test_rejects_destination_inside_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "source"
            source.mkdir()
            manifest = self.write_manifest(source, ("PUBLIC-MANIFEST.txt",))
            with self.assertRaisesRegex(AssemblyError, "inside source"):
                assemble(source, source / "assembled", manifest)

    def test_rejects_malformed_manifest_with_blank_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            manifest = source / "PUBLIC-MANIFEST.txt"
            manifest.write_text("PUBLIC-MANIFEST.txt\n\nsafe.txt\n", encoding="utf-8")
            with self.assertRaisesRegex(AssemblyError, "blank"):
                assemble(source, root / "destination", manifest)

    def test_rejects_unsorted_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            manifest = self.write_manifest(source, ("safe.txt", "PUBLIC-MANIFEST.txt"))
            with self.assertRaisesRegex(AssemblyError, "sorted"):
                assemble(source, root / "destination", manifest)

    def test_rejects_manifest_that_does_not_list_itself(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            (source / "safe.txt").write_text("safe\n", encoding="utf-8")
            manifest = self.write_manifest(source, ("safe.txt",))
            with self.assertRaisesRegex(AssemblyError, "list itself"):
                assemble(source, root / "destination", manifest)

    def test_rejects_manifest_outside_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            manifest = root / "PUBLIC-MANIFEST.txt"
            manifest.write_text("PUBLIC-MANIFEST.txt\n", encoding="utf-8")
            with self.assertRaisesRegex(AssemblyError, "manifest must be inside source"):
                assemble(source, root / "destination", manifest)

    def test_rejects_non_utf8_manifested_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            (source / "invalid.txt").write_bytes(bytes((255, 254)))
            manifest = self.write_manifest(
                source,
                ("PUBLIC-MANIFEST.txt", "invalid.txt"),
            )
            with self.assertRaisesRegex(AssemblyError, "UTF-8"):
                assemble(source, root / "destination", manifest)

    def test_rejects_unsupported_manifested_file_type(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            (source / "payload.bin").write_bytes(b"binary")
            manifest = self.write_manifest(
                source,
                ("PUBLIC-MANIFEST.txt", "payload.bin"),
            )
            with self.assertRaisesRegex(AssemblyError, "unsupported public file type"):
                assemble(source, root / "destination", manifest)

    def test_rejects_malformed_svg(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            (source / "broken.svg").write_text("<svg>", encoding="utf-8")
            manifest = self.write_manifest(
                source,
                ("PUBLIC-MANIFEST.txt", "broken.svg"),
            )
            with self.assertRaisesRegex(AssemblyError, "approved SVG"):
                assemble(source, root / "destination", manifest)

    def test_rejects_symlink_manifest_and_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            real_manifest = source / "real-manifest.txt"
            real_manifest.write_text("manifest-link.txt\n", encoding="utf-8")
            manifest_link = source / "manifest-link.txt"
            os.symlink(real_manifest, manifest_link)
            with self.assertRaisesRegex(AssemblyError, "manifest must be a regular non-symlink file"):
                assemble(source, root / "destination", manifest_link)

            real_manifest.write_text("real-manifest.txt\n", encoding="utf-8")
            real_destination = root / "real-destination"
            real_destination.mkdir()
            destination_link = root / "destination-link"
            os.symlink(real_destination, destination_link)
            with self.assertRaisesRegex(AssemblyError, "destination must not be a symlink"):
                assemble(source, destination_link, real_manifest)


if __name__ == "__main__":
    unittest.main()
