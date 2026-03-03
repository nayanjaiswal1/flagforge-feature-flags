from unittest.mock import Mock

from fastapi import HTTPException, Request
import pytest

from flagforge.contrib.fastapi.context import context_factory
from flagforge.contrib.fastapi.dependencies import get_engine, get_storage


def test_context_factory_headers():
    request = Mock(spec=Request)
    request.headers = {"X-Tenant-ID": "t1", "X-User-ID": "u1"}
    request.scope = {}

    ctx = context_factory(request)
    assert ctx.tenant_id == "t1"
    assert ctx.user_id == "u1"


def test_context_factory_state():
    request = Mock(spec=Request)
    request.headers = {}
    request.state.tenant_id = "t2"
    request.state.flagforge_attrs = {"attr": "val"}
    request.scope = {}

    ctx = context_factory(request)
    assert ctx.tenant_id == "t2"
    assert ctx.attributes == {"attr": "val"}


def test_context_factory_auth():
    request = Mock(spec=Request)
    request.headers = {}
    request.scope = {"auth": True, "user": True}

    # Mock request.auth
    request.auth = Mock()
    request.auth.sub = "u_auth"
    # Mock request.user
    request.user = Mock()
    request.user.id = "u_user"  # String or int

    # User ID priority: headers > auth > user?
    # Logic:
    # if not user_id and auth...
    # if not user_id and user...
    # So auth wins if present and sets user_id.

    ctx = context_factory(request)
    assert ctx.user_id == "u_auth"


def test_context_factory_user_fallback():
    request = Mock(spec=Request)
    request.headers = {}
    request.scope = {"user": True}
    request.auth = None

    request.user = Mock()
    request.user.id = 123
    group = Mock()
    group.name = "g1"
    request.user.groups.all.return_value = [group]

    ctx = context_factory(request)
    assert ctx.user_id == "123"
    assert ctx.group_ids == ["g1"]


def test_dependencies_missing_engine():
    request = Mock(spec=Request)
    request.app.state = Mock()
    # Ensure getattr returns None
    del request.app.state.flagforge_engine

    # getattr(obj, name, default) handles missing attr
    # But Mock creates attrs on access.
    # So we need request.app.state not to have the attr.
    # Or mock getattr?
    # dependencies.py uses: getattr(request.app.state, "flagforge_engine", None)
    # If request.app.state is a Mock, getattr returns a Mock by default.
    # We need to ensure it returns None.

    # Proper way with Mock:
    # configure mock to raise AttributeError or set spec
    request.app.state = object()  # Basic object has no attrs

    with pytest.raises(HTTPException) as exc:
        get_engine(request)
    assert exc.value.status_code == 500
    assert "not configured" in exc.value.detail


def test_dependencies_missing_storage():
    request = Mock(spec=Request)
    request.app.state = object()

    with pytest.raises(HTTPException) as exc:
        get_storage(request)
    assert exc.value.status_code == 500
    assert "not configured" in exc.value.detail
