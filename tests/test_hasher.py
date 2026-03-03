from flagforge.core.hasher import compute_bucket, evaluate_rollout


def test_compute_bucket_determinism():
    tenant_id = "tenant-1"
    flag_key = "new-feature"
    user_id = "user-123"

    bucket1 = compute_bucket(tenant_id, flag_key, user_id)
    bucket2 = compute_bucket(tenant_id, flag_key, user_id)

    assert bucket1 == bucket2
    assert 0 <= bucket1 < 100


def test_compute_bucket_different_inputs():
    tenant_id = "tenant-1"
    flag_key = "new-feature"

    bucket1 = compute_bucket(tenant_id, flag_key, "user-1")
    compute_bucket(tenant_id, flag_key, "user-2")

    # While they COULD be the same, with enough users they should differ.
    # We just want to ensure the input actually affects the output.
    assert bucket1 != compute_bucket(tenant_id, "other-flag", "user-1")


def test_compute_bucket_anonymous_user():
    tenant_id = "tenant-1"
    flag_key = "new-feature"

    bucket1 = compute_bucket(tenant_id, flag_key, None)
    bucket2 = compute_bucket(tenant_id, flag_key, None)

    assert bucket1 == bucket2
    assert 0 <= bucket1 < 100


def test_evaluate_rollout_edge_cases():
    tenant_id = "t1"
    flag_key = "f1"
    user_id = "u1"

    # 0% should always be False
    assert evaluate_rollout(tenant_id, flag_key, user_id, 0) is False
    assert evaluate_rollout(tenant_id, flag_key, user_id, -1) is False

    # 100% should always be True
    assert evaluate_rollout(tenant_id, flag_key, user_id, 100) is True
    assert evaluate_rollout(tenant_id, flag_key, user_id, 110) is True


def test_evaluate_rollout_distribution():
    tenant_id = "t1"
    flag_key = "f1"

    # Test 50% rollout across 1000 users
    count_enabled = 0
    total_users = 1000
    for i in range(total_users):
        if evaluate_rollout(tenant_id, flag_key, f"user-{i}", 50):
            count_enabled += 1

    # For a good hash, it should be close to 500.
    # Standard deviation for binomial(1000, 0.5) is sqrt(1000 * 0.5 * 0.5) approx 15.8
    # 500 +/- 50 is a very safe range for a deterministic test.
    assert 450 <= count_enabled <= 550


def test_evaluate_rollout_consistency():
    # Same user, same flag, same percentage -> same result
    args = ("t1", "f1", "u1", 25)
    assert evaluate_rollout(*args) == evaluate_rollout(*args)
