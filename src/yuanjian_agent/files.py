from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from .models import ScanLimits


IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "site-packages",
}

TEXT_SUFFIXES = {
    ".py",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".toml",
    ".md",
    ".rst",
    ".txt",
    ".env",
    ".ini",
    ".cfg",
    ".conf",
    ".sh",
    ".ps1",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".properties",
    ".bash",
    ".pem",
    ".key",
}

SPECIAL_TEXT_NAMES = {
    ".env",
    ".env.example",
    ".gitignore",
    "Dockerfile",
    "requirements.txt",
    "bash",
    "id_rsa",
    "id_ecdsa",
    "id_ed25519",
}


@dataclass(slots=True)
class TextFile:
    path: Path
    relative_path: str
    text: str = field(repr=False)


def looks_binary(data: bytes) -> bool:
    if b"\x00" in data:
        return True
    if not data:
        return False
    sample = data[:4096]
    controls = sum(byte < 9 or 13 < byte < 32 for byte in sample)
    return controls / len(sample) > 0.10


def _iter_source_paths(root: Path, warnings: list[str]) -> Iterator[Path]:
    def on_error(_error: OSError) -> None:
        warnings.append("Could not read a source directory; diagnostic details suppressed")

    for directory, subdirectories, filenames in os.walk(root, topdown=True, onerror=on_error, followlinks=False):
        parent = Path(directory)
        retained = []
        for name in subdirectories:
            path = parent / name
            try:
                is_symlink = path.is_symlink()
            except OSError as error:
                on_error(error)
                continue
            if is_symlink:
                warnings.append(f"Skipped symbolic link: {path.relative_to(root).as_posix()}")
            elif name not in IGNORED_DIRS:
                retained.append(name)
        # Prune before walking: filtering files after rglob still visits every
        # directory in virtual environments, dependency trees and VCS metadata.
        subdirectories[:] = retained
        for name in filenames:
            yield parent / name


def iter_text_files(root: Path, limits: ScanLimits) -> tuple[list[TextFile], list[str]]:
    files: list[TextFile] = []
    warnings: list[str] = []
    total = 0
    for path in _iter_source_paths(root, warnings):
        try:
            if path.is_symlink():
                warnings.append(f"Skipped symbolic link: {path.relative_to(root).as_posix()}")
                continue
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if (path.name not in SPECIAL_TEXT_NAMES and path.suffix.lower() not in TEXT_SUFFIXES
                    and not path.name.startswith(".env.")):
                continue
            if len(files) >= limits.max_files:
                warnings.append(f"Stopped after {limits.max_files} files")
                break
            size = path.stat().st_size
            if size > limits.max_file_bytes:
                warnings.append(f"Skipped oversized file: {relative.as_posix()}")
                continue
            total += size
            if total > limits.max_total_bytes:
                warnings.append("Stopped at total scan-size limit")
                break
            # Bound the actual read too: a file can grow after stat().
            with path.open("rb") as source:
                data = source.read(min(limits.max_file_bytes, limits.max_total_bytes - total + size) + 1)
            if len(data) > limits.max_file_bytes:
                warnings.append("Skipped oversized file; diagnostic details suppressed")
                continue
            total += len(data) - size
            if total > limits.max_total_bytes:
                warnings.append("Stopped at total scan-size limit")
                break
            if looks_binary(data):
                warnings.append(f"Skipped binary file: {relative.as_posix()}")
                continue
            text = data.decode("utf-8", errors="replace")
            files.append(TextFile(path=path, relative_path=relative.as_posix(), text=text))
        except (OSError, ValueError):
            warnings.append("Could not read a source file; diagnostic details suppressed")
    return files, warnings
