from django.template import Context, Template
from django.test import RequestFactory
import pytest

from flagforge.contrib.django.models import FeatureFlagDefinition


@pytest.mark.django_db
def test_is_flag_enabled_tag():
    FeatureFlagDefinition.objects.create(key="f1", name="F1", is_public=True, default_enabled=True)

    # We need a request for the template tag to use
    factory = RequestFactory()
    request = factory.get("/")
    request.tenant_id = "t1"

    # Configure global engine for Django contrib
    # (Django contrib uses singleton _engine in views/engine.py)
    from flagforge.contrib.django.engine import get_engine

    get_engine()

    out = Template("{% load flagforge %}{% is_flag_enabled 'f1' as f1_on %}{{ f1_on }}").render(
        Context({"request": request})
    )

    assert out.strip() == "True"


@pytest.mark.django_db
def test_flag_enabled_filter():
    FeatureFlagDefinition.objects.create(key="f1", name="F1", is_public=True, default_enabled=False)

    factory = RequestFactory()
    request = factory.get("/")
    request.tenant_id = "t1"

    out = Template("{% load flagforge %}{{ request|flag_enabled_filter:'f1' }}").render(
        Context({"request": request})
    )

    assert out.strip() == "False"
