"""Tests for the resolution logic."""

from typing import Any

from flagforge.core.context import FeatureContext
from flagforge.core.models import FlagDefinition, TenantOverride
from flagforge.core.resolver import resolve


def defn(**kwargs) -> FlagDefinition:
    defaults: dict[str, Any] = {"key": "f", "name": "F", "default_enabled": False}
    defaults.update(kwargs)
    return FlagDefinition(**defaults)


def override(**kwargs) -> TenantOverride:
    defaults: dict[str, Any] = {"key": "f", "tenant_id": "t1"}
    defaults.update(kwargs)
    return TenantOverride(**defaults)


def ctx(**kwargs) -> FeatureContext:
    defaults: dict[str, Any] = {"tenant_id": "t1"}
    defaults.update(kwargs)
    return FeatureContext(**defaults)


class TestResolve:
    def test_default_disabled_no_override(self):
        assert resolve(defn(default_enabled=False), None, ctx()) is False

    def test_default_enabled_no_override(self):
        assert resolve(defn(default_enabled=True), None, ctx()) is True

    def test_override_enables(self):
        assert resolve(defn(default_enabled=False), override(enabled=True), ctx()) is True

    def test_override_disables(self):
        assert resolve(defn(default_enabled=True), override(enabled=False), ctx()) is False

    def test_user_targeting_beats_override_disabled(self):
        result = resolve(
            defn(default_enabled=False),
            override(enabled=False, enabled_for_users=["u1"]),
            ctx(user_id="u1"),
        )
        assert result is True

    def test_group_targeting_beats_override_disabled(self):
        result = resolve(
            defn(default_enabled=False),
            override(enabled=False, enabled_for_groups=["beta"]),
            ctx(group_ids=["beta"]),
        )
        assert result is True

    def test_environment_gate_blocks(self):
        result = resolve(
            defn(default_enabled=True, environments=["prod"]),
            None,
            ctx(environment="dev"),
        )
        assert result is False

    def test_environment_gate_allows(self):
        result = resolve(
            defn(default_enabled=True, environments=["prod"]),
            None,
            ctx(environment="prod"),
        )
        assert result is True

    def test_no_environment_in_context(self):
        # Flag restricted to prod, context has no env → blocked
        result = resolve(
            defn(default_enabled=True, environments=["prod"]),
            None,
            ctx(environment=None),
        )
        assert result is False

    def test_rollout_100_percent(self):
        result = resolve(
            defn(default_enabled=True, rollout_percentage=100),
            None,
            ctx(user_id="any_user"),
        )
        assert result is True

    def test_rollout_0_percent_with_default_enabled(self):
        # rollout_percentage=0 means fully on (no bucketing)
        result = resolve(
            defn(default_enabled=True, rollout_percentage=0),
            None,
            ctx(user_id="any_user"),
        )
        assert result is True
