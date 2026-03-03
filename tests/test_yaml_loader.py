"""Tests for the YAML loader."""

from pathlib import Path

import pytest

from flagforge.core.exceptions import StorageError
from flagforge.storage.memory import InMemoryStorage
from flagforge.storage.yaml_loader import load_flags, sync_from_yaml

SAMPLE_YAML = """
flags:
  new_dashboard:
    name: New Dashboard
    description: Redesigned UI
    default_enabled: false
    is_public: true
    rollout_percentage: 0

  dark_mode:
    name: Dark Mode
    default_enabled: true
    is_public: true
    rollout_percentage: 0
    environments:
      - staging
      - production
"""


class TestParseYamlFlags:
    def test_parses_valid_yaml(self, tmp_path):
        p = tmp_path / "flags.yaml"
        p.write_text(SAMPLE_YAML)
        flags = load_flags(p)
        keys = {f.key for f in flags}
        assert "new_dashboard" in keys
        assert "dark_mode" in keys

    def test_flag_fields(self, tmp_path):
        p = tmp_path / "flags.yaml"
        p.write_text(SAMPLE_YAML)
        flags = {f.key: f for f in load_flags(p)}
        assert flags["new_dashboard"].default_enabled is False
        assert flags["new_dashboard"].is_public is True
        assert flags["dark_mode"].default_enabled is True
        assert flags["dark_mode"].environments == ["staging", "production"]

    def test_missing_file_raises(self):
        with pytest.raises(StorageError, match="not found"):
            load_flags(Path("/nonexistent/flags.yaml"))

    def test_invalid_rollout_raises(self, tmp_path):
        p = tmp_path / "flags.yaml"
        p.write_text("flags:\n  f:\n    name: F\n    rollout_percentage: 999\n")
        with pytest.raises(StorageError):
            load_flags(p)


class TestSyncFromYaml:
    def test_sync_inserts_flags(self, tmp_path):
        p = tmp_path / "flags.yaml"
        p.write_text(SAMPLE_YAML)
        storage = InMemoryStorage()
        sync_from_yaml(storage, p)
        definitions = storage.get_all_definitions()
        keys = {d.key for d in definitions}
        assert "new_dashboard" in keys
        assert "dark_mode" in keys

    def test_sync_is_idempotent(self, tmp_path):
        p = tmp_path / "flags.yaml"
        p.write_text(SAMPLE_YAML)
        storage = InMemoryStorage()
        sync_from_yaml(storage, p)
        sync_from_yaml(storage, p)
        assert len(storage.get_all_definitions()) == 2

    def test_remove_deprecated(self, tmp_path):
        p1 = tmp_path / "flags1.yaml"
        p1.write_text(SAMPLE_YAML)
        storage = InMemoryStorage()
        sync_from_yaml(storage, p1)
        assert len(storage.get_all_definitions()) == 2

        p2 = tmp_path / "flags2.yaml"
        p2.write_text("flags:\n  new_dashboard:\n    name: New Dashboard\n")
        sync_from_yaml(storage, p2, remove_deprecated=True)
        keys = {d.key for d in storage.get_all_definitions()}
        assert "dark_mode" not in keys
        assert "new_dashboard" in keys
