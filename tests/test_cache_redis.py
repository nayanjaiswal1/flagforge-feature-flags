from fakeredis import FakeAsyncRedis, FakeRedis
import pytest

from flagforge.cache.redis import AsyncRedisCache, RedisCache


@pytest.fixture
def redis_client():
    return FakeRedis(decode_responses=True)


@pytest.fixture
def async_redis_client():
    return FakeAsyncRedis(decode_responses=True)


def test_redis_cache_sync(redis_client, monkeypatch):
    # Mock redis client in RedisCache
    monkeypatch.setattr("flagforge.cache.redis.redis.Redis", lambda **kwargs: redis_client)

    cache = RedisCache("redis://localhost")
    cache._redis = redis_client  # Ensure we use our fixture instance

    # Basic get/set
    assert cache.get("k1") is None
    cache.set("k1", True)
    assert cache.get("k1") is True

    # Delete
    cache.delete("k1")
    assert cache.get("k1") is None

    # Pattern delete (flag)
    # Keys: prefix:tenant:user:env
    # RedisCache defaults: prefix="flagforge"
    # key structure in RedisCache: {prefix}:{key}

    cache.set("f1:t1:u1", True)
    cache.set("f1:t2:u1", True)
    cache.set("f2:t1:u1", True)

    cache.delete_for_flag("f1")
    assert cache.get("f1:t1:u1") is None
    assert cache.get("f1:t2:u1") is None
    assert cache.get("f2:t1:u1") is True

    # Pattern delete (tenant)
    cache.set("f2:t1:u1", True)
    cache.set("f2:t2:u1", True)
    cache.set("other:t1:u1", True)

    # delete_for_tenant scans for *:{tenant_id}:*
    # We need to ensure our keys match the pattern expected by delete_for_tenant
    # The implementation does: match=f"{self.key_prefix}*:{tenant_id}:*"
    # So if key_prefix is "flagforge", it looks for "flagforge*:t1:*"

    # Let's verify how keys are constructed in the cache vs engine.
    # The cache backend just takes a key string. The engine constructs it.
    # The engine constructs: {flag}:{tenant}:{user}:{env}
    # RedisCache prepends "flagforge:" -> "flagforge:{flag}:{tenant}:{user}:{env}"

    # So for tenant "t1", we expect "flagforge:*:t1:*"

    # Re-set with proper structure for tenant delete test
    cache.set("f1:t1:u1", True)  # -> flagforge:f1:t1:u1
    cache.set("f1:t2:u1", True)  # -> flagforge:f1:t2:u1
    cache.set("f2:t1:u1", True)  # -> flagforge:f2:t1:u1

    cache.delete_for_tenant("t1")

    assert cache.get("f1:t1:u1") is None
    assert cache.get("f2:t1:u1") is None
    assert cache.get("f1:t2:u1") is True


@pytest.mark.asyncio
async def test_redis_cache_async(async_redis_client, monkeypatch):
    monkeypatch.setattr(
        "flagforge.cache.redis.redis.asyncio.from_url", lambda url, **kw: async_redis_client
    )

    cache = AsyncRedisCache("redis://localhost")
    # For async, we can't easily monkeypatch the init call inside the class perfectly
    # without deeper mocking because it calls from_url.
    # But we can just set the _redis attribute manually for the test.
    cache._redis = async_redis_client

    await cache.set("k1", True)
    assert await cache.get("k1") is True

    await cache.delete("k1")
    assert await cache.get("k1") is None

    # Test delete logic
    # Use keys that match the structure expected by delete_for_tenant (:tenant_id:)
    await cache.set("f1:t1:x", True)
    await cache.set("f2:t1:x", True)

    await cache.delete_for_flag("f1")
    assert await cache.get("f1:t1:x") is None
    assert await cache.get("f2:t1:x") is True

    await cache.delete_for_tenant("t1")
    assert await cache.get("f2:t1:x") is None
