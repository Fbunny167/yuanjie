"""File-policy tests exercise the shared reader used by ScanEngine."""
import io
import json
import os
from pathlib import Path

import pytest

from yuanjian_agent.config import Settings
from yuanjian_agent.engine import ScanEngine
from yuanjian_agent.files import IGNORED_DIRS, iter_text_files
from yuanjian_agent.models import ScanLimits


RAW = "sk-test-8KJd82kdlQ93kdl20f"


@pytest.mark.parametrize("name", ["code.py", "code.js", "code.jsx", "code.ts", "code.tsx",
    "code.java", "code.go", "code.rs", ".env", ".env.production", "config.yaml",
    "settings.yml", "config.json", "secrets.toml", "config.ini", "config.conf",
    "application.properties", "code.sh", "script.bash", "bash", "docker-compose.yml",
    "docker-compose.yaml", "key.pem", "id_ed25519"])
def test_required_source_and_configuration_files(tmp_path, name):
    (tmp_path / name).write_text(f'API_KEY="{RAW}"', encoding="utf-8")
    files, warnings = iter_text_files(tmp_path, ScanLimits())
    assert [f.relative_path for f in files] == [name]
    assert not warnings


def test_skip_binary_file(tmp_path):
    (tmp_path / "binary.py").write_bytes(b"\x00API_KEY=synthetic")
    files, warnings = iter_text_files(tmp_path, ScanLimits())
    assert not files and any("binary" in warning for warning in warnings)


@pytest.mark.parametrize("suffix", [".png", ".mp4", ".pt", ".zip", ".sqlite", ".unknown"])
def test_skip_unsupported_file(tmp_path, suffix):
    (tmp_path / ("file" + suffix)).write_text(f'API_KEY="{RAW}"', encoding="utf-8")
    files, warnings = iter_text_files(tmp_path, ScanLimits())
    assert not files and not warnings


def test_skip_large_file(tmp_path):
    (tmp_path / "huge.py").write_text("x" * 65, encoding="utf-8")
    files, warnings = iter_text_files(tmp_path, ScanLimits(max_file_bytes=64))
    assert not files and any("oversized" in warning for warning in warnings)


def test_skip_ignored_directories(tmp_path):
    for directory in IGNORED_DIRS:
        target = tmp_path / directory
        target.mkdir()
        (target / "config.py").write_text(f'API_KEY="{RAW}"', encoding="utf-8")
    files, _ = iter_text_files(tmp_path, ScanLimits())
    assert not files


@pytest.mark.parametrize("directory", sorted(IGNORED_DIRS))
def test_ignored_directories_are_not_traversed(tmp_path, monkeypatch, directory):
    project = tmp_path / "project"
    project.mkdir()
    ignored = project / "src" / directory
    ignored.mkdir(parents=True)
    (ignored / "config.py").write_text("ignored = True", encoding="utf-8")
    (project / "src" / "main.py").write_text("value = 1", encoding="utf-8")
    original = os.scandir

    def scandir(path):
        assert Path(path) != ignored, "The scanner entered an ignored directory"
        return original(path)

    monkeypatch.setattr(os, "scandir", scandir)
    files, warnings = iter_text_files(project, ScanLimits())
    assert [file.relative_path for file in files] == ["src/main.py"]
    assert not warnings


@pytest.mark.parametrize("failure", ["enumeration", "metadata"])
def test_directory_read_errors_are_reported_without_exception_details(tmp_path, monkeypatch, failure):
    denied = tmp_path / "denied"
    denied.mkdir()
    (tmp_path / "main.py").write_text("value = 1", encoding="utf-8")
    original = os.scandir
    original_is_symlink = Path.is_symlink

    def scandir(path):
        if failure == "enumeration" and Path(path) == denied:
            raise PermissionError(RAW)
        return original(path)

    def is_symlink(path):
        if failure == "metadata" and path == denied:
            raise PermissionError(RAW)
        return original_is_symlink(path)

    monkeypatch.setattr(os, "scandir", scandir)
    monkeypatch.setattr(Path, "is_symlink", is_symlink)
    files, warnings = iter_text_files(tmp_path, ScanLimits())
    assert [file.relative_path for file in files] == ["main.py"]
    assert warnings == ["Could not read a source directory; diagnostic details suppressed"]
    assert RAW not in json.dumps(warnings)


@pytest.mark.parametrize("directory", [False, True], ids=["file", "directory"])
def test_symbolic_links_are_skipped_with_a_warning(tmp_path, directory):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    if directory:
        outside.mkdir()
        (outside / "config.py").write_text("outside = True", encoding="utf-8")
    else:
        outside.write_text("outside = True", encoding="utf-8")
    link = project / ("linked" if directory else "linked.py")
    try:
        link.symlink_to(outside, target_is_directory=directory)
    except OSError:
        pytest.skip("Symbolic link creation is unavailable")

    files, warnings = iter_text_files(project, ScanLimits())
    assert not files
    assert warnings == [f"Skipped symbolic link: {link.name}"]


def test_actual_read_is_bounded_if_file_grows(tmp_path, monkeypatch):
    target = tmp_path / "config.py"
    target.write_text("small", encoding="utf-8")
    original = Path.open
    read_sizes = []

    class GrowingStream(io.BytesIO):
        def read(self, size=-1):
            read_sizes.append(size)
            return super().read(size)

    def opened(path, mode="r", *args, **kwargs):
        if path == target and mode == "rb":
            return GrowingStream(b"x" * 1000)
        return original(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", opened)
    files, warnings = iter_text_files(tmp_path, ScanLimits(max_file_bytes=64))
    assert read_sizes == [65]
    assert not files and warnings


@pytest.mark.parametrize("error_type", [PermissionError, FileNotFoundError, UnicodeDecodeError])
def test_unreadable_file_does_not_break_engine_or_leak_diagnostic(tmp_path, monkeypatch, caplog, error_type):
    project = tmp_path / "input"
    project.mkdir()
    bad = project / "bad.py"
    bad.write_text("bad", encoding="utf-8")
    (project / "good.py").write_text(f'API_KEY="{RAW}"', encoding="utf-8")
    original = Path.open

    def opened(path, mode="r", *args, **kwargs):
        if path == bad and mode == "rb":
            if error_type is UnicodeDecodeError:
                raise UnicodeDecodeError("utf8", RAW.encode(), 0, 1, RAW)
            raise error_type(RAW)
        return original(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", opened)
    engine = ScanEngine(Settings(data_dir=tmp_path / "state"))
    result = engine.scan(project)
    assert result.summary.secrets == 1
    assert result.metadata["scanners"]["agent_security"]["status"] == "success"
    assert any("Could not read" in warning for warning in result.warnings)
    assert RAW not in json.dumps(result.to_dict()) + caplog.text
