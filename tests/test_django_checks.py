from django.test import override_settings

from flagforge.contrib.django.checks import check_tenancy_mode


def test_check_settings_success():
    # Should pass with default test settings
    errors = check_tenancy_mode(None)
    assert errors == []


@override_settings(FLAGFORGE_TENANCY_MODE="invalid")
def test_check_settings_invalid_mode():
    errors = check_tenancy_mode(None)
    assert len(errors) == 1
    assert errors[0].id == "flagforge.E001"
