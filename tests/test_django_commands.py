from django.core.management import call_command
import pytest

from flagforge.contrib.django.models import FeatureFlagDefinition, TenantFeatureFlag


@pytest.mark.django_db
def test_sync_feature_flags_command(tmp_path):
    # Create a test YAML
    yaml_file = tmp_path / "flags.yaml"
    yaml_file.write_text("""
flags:
  new_ui:
    name: New UI
    default_enabled: true
  beta_feature:
    name: Beta
    default_enabled: false
""")

    call_command("sync_feature_flags", config=str(yaml_file))

    assert FeatureFlagDefinition.objects.filter(key="new_ui").exists()
    assert FeatureFlagDefinition.objects.get(key="new_ui").default_enabled is True
    assert FeatureFlagDefinition.objects.filter(key="beta_feature").exists()


@pytest.mark.django_db
def test_enable_disable_flag_commands():
    f1 = FeatureFlagDefinition.objects.create(key="f1", name="F1")

    # Enable
    call_command("enable_flag_for_tenant", flag="f1", tenant="t1")
    assert TenantFeatureFlag.objects.get(key=f1, tenant_id="t1").enabled is True

    # Disable
    call_command("disable_flag_for_tenant", flag="f1", tenant="t1")
    assert TenantFeatureFlag.objects.get(key=f1, tenant_id="t1").enabled is False


@pytest.mark.django_db
def test_show_flag_status_command(capsys):
    f1 = FeatureFlagDefinition.objects.create(key="f1", name="F1", default_enabled=True)
    TenantFeatureFlag.objects.create(key=f1, tenant_id="t1", enabled=False)

    call_command("show_flag_status", flag="f1", tenant="t1")
    captured = capsys.readouterr()
    assert "f1" in captured.out
    assert "DISABLED" in captured.out
