from unittest.mock import Mock

import pytest


@pytest.mark.django_db
def test_cli_command_exception(monkeypatch):
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "tests.django_settings")

    # Mock engine to raise exception
    mock_engine = Mock()
    mock_engine.is_enabled.side_effect = Exception("Boom")

    # We need to inject this engine.
    # The CLI creates engine internally using _get_engine.
    # We can mock _get_engine in the module.
    # But _get_engine is a local function inside cli? No, it's module level?
    # Let's check main.py structure again.
    pass
