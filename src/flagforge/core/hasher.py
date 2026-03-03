"""Deterministic rollout hashing using MurmurHash3."""

import mmh3


def compute_bucket(tenant_id: str, flag_key: str, user_id: str | None) -> int:
    """Compute bucket value (0-99) for a user/flag combination.

    Uses MurmurHash3 for fast, deterministic bucketing.
    Same inputs always produce the same bucket.

    Args:
        tenant_id: Tenant identifier
        flag_key: Feature flag key
        user_id: User identifier (None for anonymous users)

    Returns:
        Bucket value from 0-99
    """
    user_part = user_id if user_id is not None else ""
    key = f"{tenant_id}:{flag_key}:{user_part}"

    # mmh3.hash returns a signed 32-bit integer
    # Use signed=False to get unsigned, then mod 100 for bucket
    hash_value = mmh3.hash(key, signed=False)
    bucket: int = int(hash_value) % 100

    return bucket


def evaluate_rollout(tenant_id: str, flag_key: str, user_id: str | None, percentage: int) -> bool:
    """Evaluate if a user falls within the rollout percentage.

    Shortcuts:
    - percentage >= 100: Always returns True
    - percentage <= 0: Always returns False

    Args:
        tenant_id: Tenant identifier
        flag_key: Feature flag key
        user_id: User identifier (None for anonymous users)
        percentage: Rollout percentage (0-100)

    Returns:
        True if user is in rollout, False otherwise
    """
    # Shortcuts for edge cases
    if percentage >= 100:
        return True
    if percentage <= 0:
        return False

    bucket = compute_bucket(tenant_id, flag_key, user_id)
    return bucket < percentage
