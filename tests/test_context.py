import pytest

from flagforge.core.context import (
    FeatureContext,
    async_request_context,
    get_request_cache,
    request_context,
)


def test_request_context_sync():
    assert get_request_cache() is None

    with request_context() as cache:
        assert get_request_cache() is cache
        cache["foo"] = "bar"
        assert get_request_cache()["foo"] == "bar"

    assert get_request_cache() is None


@pytest.mark.asyncio
async def test_request_context_async():
    assert get_request_cache() is None

    async with async_request_context() as cache:
        assert get_request_cache() is cache
        cache["foo"] = "bar"
        assert get_request_cache()["foo"] == "bar"

    assert get_request_cache() is None


def test_feature_context_defaults():
    ctx = FeatureContext()
    assert ctx.tenant_id is None
    assert ctx.user_id is None
    assert ctx.group_ids == []
    assert ctx.environment is None
    assert ctx.attributes == {}


def test_feature_context_custom_values():
    ctx = FeatureContext(
        tenant_id="t1",
        user_id="u1",
        group_ids=["g1"],
        environment="prod",
        attributes={"attr1": "val1"},
    )
    assert ctx.tenant_id == "t1"
    assert ctx.user_id == "u1"
    assert ctx.group_ids == ["g1"]
    assert ctx.environment == "prod"
    assert ctx.attributes == {"attr1": "val1"}
