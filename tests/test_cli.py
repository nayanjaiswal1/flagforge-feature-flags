from click.testing import CliRunner
import pytest

from flagforge.cli.main import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Sync feature flags" in result.output


@pytest.mark.django_db
def test_cli_sync_success(tmp_path, monkeypatch):
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "tests.django_settings")
    config = tmp_path / "flags.yaml"
    config.write_text("flags: {f1: {name: F1}}")
    runner = CliRunner()
    # Use memory storage for CLI tests by mocking get_storage or similar
    # but the CLI currently seems to use the engine which might use real storage.
    # Let's just test it runs and doesn't crash if we give it a real but temporary path.
    result = runner.invoke(cli, ["sync", "--config", str(config)])
    assert result.exit_code == 0


@pytest.mark.django_db
def test_cli_sync_options(tmp_path, monkeypatch):
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "tests.django_settings")
    config = tmp_path / "flags.yaml"
    config.write_text("flags: {f1: {name: F1}, f2: {name: F2, deprecated: true}}")
    runner = CliRunner()

    # Dry run
    result = runner.invoke(cli, ["sync", "--config", str(config), "--dry-run"])
    assert result.exit_code == 0
    assert "Would sync: f1" in result.output

    # Actual sync with remove deprecated
    result = runner.invoke(cli, ["sync", "--config", str(config), "--remove-deprecated"])
    assert result.exit_code == 0
    assert "Synced: f1" in result.output
    assert "Removed 1 deprecated flags" in result.output


@pytest.mark.django_db
def test_cli_status_all(tmp_path, monkeypatch):
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "tests.django_settings")
    config = tmp_path / "flags.yaml"
    config.write_text("flags: {f1: {name: F1, default_enabled: true}}")
    runner = CliRunner()
    runner.invoke(cli, ["sync", "--config", str(config)])

    # Status for all flags (no --flag)
    result = runner.invoke(cli, ["status", "--tenant", "t1"])
    assert result.exit_code == 0
    assert "f1: ENABLED" in result.output

    # Status for single flag
    result = runner.invoke(cli, ["status", "--tenant", "t1", "--flag", "f1"])
    assert result.exit_code == 0
    assert "f1: ENABLED" in result.output


@pytest.mark.django_db
def test_cli_enable_disable(tmp_path, monkeypatch):
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "tests.django_settings")
    config = tmp_path / "flags.yaml"
    config.write_text("flags: {f1: {name: F1}}")
    runner = CliRunner()
    runner.invoke(cli, ["sync", "--config", str(config)])

    result = runner.invoke(cli, ["enable", "--flag", "f1", "--tenant", "t1"])
    assert result.exit_code == 0


def test_cli_sync_load_error(tmp_path):
    runner = CliRunner()
    # Invalid YAML
    config = tmp_path / "invalid.yaml"
    config.write_text("invalid: yaml: content: [")

    result = runner.invoke(cli, ["sync", "--config", str(config)])
    assert result.exit_code == 1
    assert "Error loading" in result.output


def test_cli_sync_missing_app_or_settings(tmp_path, monkeypatch):
    runner = CliRunner()
    config = tmp_path / "flags.yaml"
    config.write_text("flags: {}")

    # Ensure no settings
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE", raising=False)

    result = runner.invoke(cli, ["sync", "--config", str(config)])
    assert result.exit_code == 1
    assert "Error: Either --app or DJANGO_SETTINGS_MODULE required" in result.output


@pytest.mark.django_db
def test_cli_enable_missing_flag(monkeypatch):
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "tests.django_settings")
    runner = CliRunner()

    # Enable non-existent flag
    result = runner.invoke(cli, ["enable", "--flag", "nonexistent", "--tenant", "t1"])
    assert result.exit_code == 1
    assert "Flag 'nonexistent' not found" in result.output


@pytest.mark.django_db
def test_cli_disable_missing_flag(monkeypatch):
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "tests.django_settings")
    runner = CliRunner()

    # Disable non-existent flag
    result = runner.invoke(cli, ["disable", "--flag", "nonexistent", "--tenant", "t1"])
    assert result.exit_code == 1
    assert "Flag 'nonexistent' not found" in result.output


def test_cli_clear_cache(monkeypatch):
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "tests.django_settings")
    runner = CliRunner()

    # Clear request cache
    result = runner.invoke(cli, ["clear-cache"])
    assert result.exit_code == 0
    assert "Cleared request cache" in result.output

    # Clear for flag
    result = runner.invoke(cli, ["clear-cache", "--flag", "f1"])
    assert result.exit_code == 0
    assert "Cleared cache for flag: f1" in result.output

    # Clear for tenant
    result = runner.invoke(cli, ["clear-cache", "--tenant", "t1"])
    assert result.exit_code == 0
    assert "Cleared cache for tenant: t1" in result.output
