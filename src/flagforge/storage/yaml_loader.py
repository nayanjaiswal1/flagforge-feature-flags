"""YAML loader for feature flag configuration files."""

from pathlib import Path

from pydantic import BaseModel, Field, ValidationError
import yaml

from flagforge.core.exceptions import StorageError
from flagforge.core.models import FlagDefinition
from flagforge.storage.base import StorageBackend


class YamlFlagDefinition(BaseModel):
    """Pydantic model for validating flag definitions from YAML.

    Attributes:
        key: Unique identifier for the flag
        name: Human-readable name
        description: Optional description
        default_enabled: Default state when no override applies
        is_public: Whether flag is exposed in public API
        rollout_percentage: Default rollout percentage (0-100)
        deprecated: Whether flag is deprecated
        environments: List of allowed environments, None means all
    """

    key: str = ""  # Injected from the YAML dict key during loading
    name: str
    description: str = ""
    default_enabled: bool = False
    is_public: bool = False
    rollout_percentage: int = Field(default=0, ge=0, le=100)
    deprecated: bool = False
    environments: list[str] | None = None


class YamlFlagConfig(BaseModel):
    """Pydantic model for validating the entire YAML config.

    Attributes:
        flags: Dictionary of flag definitions keyed by flag key
    """

    flags: dict[str, YamlFlagDefinition]


def load_yaml_config(path: str | Path) -> dict:
    """Load and parse a YAML configuration file.

    Args:
        path: Path to the YAML file

    Returns:
        Parsed YAML data as a dictionary

    Raises:
        StorageError: If file not found or YAML syntax error
    """
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError as e:
        raise StorageError(f"YAML file not found: {path}") from e
    except yaml.YAMLError as e:
        raise StorageError(f"YAML syntax error in {path}: {e}") from e


def parse_yaml_flags(data: dict) -> YamlFlagConfig:
    """Parse and validate YAML data into a YamlFlagConfig.

    Args:
        data: Parsed YAML data dictionary

    Returns:
        Validated YamlFlagConfig object

    Raises:
        StorageError: If validation fails
    """
    try:
        return YamlFlagConfig.model_validate(data)
    except ValidationError as e:
        # Format validation errors as "field: error"
        error_messages = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            error_messages.append(f"{field}: {error['msg']}")
        raise StorageError(f"YAML validation errors: {'; '.join(error_messages)}") from e


def load_flags(yaml_path: str | Path) -> list[FlagDefinition]:
    """Load flag definitions from a YAML file.

    Args:
        yaml_path: Path to the YAML file

    Returns:
        List of FlagDefinition objects

    Raises:
        StorageError: If file not found or YAML error
    """
    data = load_yaml_config(yaml_path)
    config = parse_yaml_flags(data)

    flags = []
    for flag_key, yaml_flag in config.flags.items():
        definition = FlagDefinition(
            key=flag_key,
            name=yaml_flag.name,
            description=yaml_flag.description,
            default_enabled=yaml_flag.default_enabled,
            is_public=yaml_flag.is_public,
            rollout_percentage=yaml_flag.rollout_percentage,
            deprecated=yaml_flag.deprecated,
            environments=yaml_flag.environments,
        )
        flags.append(definition)

    return flags


def sync_from_yaml(
    storage: StorageBackend, yaml_path: Path, remove_deprecated: bool = False
) -> None:
    """Synchronize flag definitions from a YAML file to storage.

    This function:
    - Loads and parses the YAML file
    - Converts each YamlFlagDefinition to a FlagDefinition
    - Upserts each flag definition (preserves existing tenant overrides)
    - Optionally removes definitions for flags not in the YAML file

    Args:
        storage: Storage backend to sync to
        yaml_path: Path to the YAML file
        remove_deprecated: If True, delete definitions not present in YAML

    Raises:
        StorageError: If file not found, YAML error, or validation error
    """
    # Load and parse YAML
    data = load_yaml_config(yaml_path)
    config = parse_yaml_flags(data)

    # Get existing definitions to track which keys exist
    existing_definitions = storage.get_all_definitions()
    existing_keys = {d.key for d in existing_definitions}

    # Upsert each flag from YAML
    yaml_keys = set()
    for flag_key, yaml_flag in config.flags.items():
        # Convert YamlFlagDefinition to FlagDefinition
        definition = FlagDefinition(
            key=flag_key,
            name=yaml_flag.name,
            description=yaml_flag.description,
            default_enabled=yaml_flag.default_enabled,
            is_public=yaml_flag.is_public,
            rollout_percentage=yaml_flag.rollout_percentage,
            deprecated=yaml_flag.deprecated,
            environments=yaml_flag.environments,
        )
        storage.upsert_definition(definition)
        yaml_keys.add(flag_key)

    # Handle deprecated flags if requested
    if remove_deprecated:
        keys_to_delete = existing_keys - yaml_keys
        for key in keys_to_delete:
            storage.delete_definition(key)
