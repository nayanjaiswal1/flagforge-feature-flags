from django.http import Http404, HttpResponse
from django.test import RequestFactory
import pytest

from flagforge.contrib.django.decorators import flag_required


def dummy_view(request):
    return HttpResponse("ok")


@pytest.mark.django_db
def test_feature_flag_decorator_enabled(monkeypatch):
    monkeypatch.setattr("flagforge.contrib.django.decorators.flag_enabled", lambda key, req: True)

    decorated = flag_required("f1")(dummy_view)
    factory = RequestFactory()
    request = factory.get("/")

    response = decorated(request)
    assert response.status_code == 200
    assert response.content == b"ok"


@pytest.mark.django_db
def test_feature_flag_decorator_disabled_404(monkeypatch):
    monkeypatch.setattr("flagforge.contrib.django.decorators.flag_enabled", lambda key, req: False)

    decorated = flag_required("f1")(dummy_view)
    factory = RequestFactory()
    request = factory.get("/")

    with pytest.raises(Http404):
        decorated(request)


@pytest.mark.django_db
def test_feature_flag_decorator_redirect(monkeypatch):
    monkeypatch.setattr("flagforge.contrib.django.decorators.flag_enabled", lambda key, req: False)

    decorated = flag_required("f1", redirect_to="/fallback")(dummy_view)
    factory = RequestFactory()
    request = factory.get("/")

    response = decorated(request)
    assert response.status_code == 302
    assert response.url == "/fallback"
