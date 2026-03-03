import pytest

from flagforge.cache.local import AsyncLocalCache, LocalCache
from flagforge.cache.null import AsyncNullCache, NullCache
from flagforge.core.context import async_request_context, request_context


def test_null_cache():
    cache = NullCache()
    assert cache.get("any") is None
    cache.set("any", True)
    assert cache.get("any") is None
    cache.delete("any")
    cache.delete_for_flag("f")
    cache.delete_for_tenant("t")
    cache.clear_request_cache()


@pytest.mark.asyncio
async def test_async_null_cache():
    cache = AsyncNullCache()
    assert await cache.get("any") is None
    await cache.set("any", True)
    assert await cache.get("any") is None
    await cache.delete("any")
    await cache.delete_for_flag("f")
    await cache.delete_for_tenant("t")
    await cache.clear_request_cache()


def test_local_cache_isolation():
    cache = LocalCache()

    # Outside context, get/set should do nothing/return None
    assert cache.get("k1") is None
    cache.set("k1", True)
    assert cache.get("k1") is None

    with request_context():
        cache.set("k1", True)
        assert cache.get("k1") is True

    # After context, should be None again
    assert cache.get("k1") is None


def test_local_cache_deletion():
    cache = LocalCache()
    with request_context():
        # Test basic delete
        cache.set("k1", True)
        cache.delete("k1")
        assert cache.get("k1") is None

        # Test delete_for_flag
        cache.set("f1", True)

        cache.set("f1:t1", True)
        cache.set("f2", True)

        cache.delete_for_flag("f1")
        assert cache.get("f1") is None
        assert cache.get("f1:t1") is None
        assert cache.get("f2") is True

        # Test delete_for_tenant
        cache.set("f1:t1", True)
        cache.set("other:t1", True)
        cache.set("f1:t2", True)

        cache.delete_for_tenant("t1")
        assert cache.get("f1:t1") is None
        assert cache.get("other:t1") is None
        assert cache.get("f1:t2") is True

        # Test clear_request_cache
        cache.set("a", True)
        cache.clear_request_cache()
        assert cache.get("a") is None


@pytest.mark.asyncio
async def test_async_local_cache():
    cache = AsyncLocalCache()
    async with async_request_context():
        await cache.set("k1", True)
        assert await cache.get("k1") is True
        await cache.delete("k1")
        assert await cache.get("k1") is None

        await cache.set("f1", True)
        await cache.clear_request_cache()
        assert await cache.get("f1") is None
