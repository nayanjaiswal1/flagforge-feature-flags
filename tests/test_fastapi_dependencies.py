from unittest.mock import Mock

from fastapi import Request

from flagforge.contrib.fastapi.dependencies import get_engine, get_request_context
from flagforge.core.context import FeatureContext


def test_get_request_context():
    # It just returns a new context currently, might be updated later to use state
    ctx = get_request_context()
    assert isinstance(ctx, FeatureContext)


def test_get_engine_success():
    request = Mock(spec=Request)
    engine_mock = Mock()
    request.app.state.flagforge_engine = engine_mock

    assert get_engine(request) is engine_mock
