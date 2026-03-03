import pytest

from flagforge.contrib.django.engine import get_engine
from flagforge.core.engine import FlagEngine


@pytest.mark.django_db
def test_django_get_engine_singleton(monkeypatch):
    # Reset global _engine
    monkeypatch.setattr("flagforge.contrib.django.engine._engine", None)

    engine1 = get_engine()
    assert isinstance(engine1, FlagEngine)

    engine2 = get_engine()
    assert engine1 is engine2
