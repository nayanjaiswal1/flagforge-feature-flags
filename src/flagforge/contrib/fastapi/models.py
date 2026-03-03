"""FastAPI SQLAlchemy models for FlagForge."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class FlagDefinition(Base):
    """Global feature flag definition."""

    __tablename__ = "feature_flag_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    default_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    rollout_percentage: Mapped[int] = mapped_column(Integer, default=0)
    deprecated: Mapped[bool] = mapped_column(Boolean, default=False)
    environments: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    tenant_overrides: Mapped[list["TenantOverride"]] = relationship(
        "TenantOverride", back_populates="flag", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<FlagDefinition(key={self.key})>"


class TenantOverride(Base):
    """Tenant-specific override for a feature flag."""

    __tablename__ = "tenant_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flag_key: Mapped[str] = mapped_column(String(255), ForeignKey("feature_flag_definitions.key"))
    tenant_id: Mapped[str] = mapped_column(String(255), index=True)
    enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    rollout_percentage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enabled_for_users: Mapped[str | None] = mapped_column(String, default="[]")
    enabled_for_groups: Mapped[str | None] = mapped_column(String, default="[]")
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    flag: Mapped["FlagDefinition"] = relationship(
        "FlagDefinition", back_populates="tenant_overrides"
    )

    __table_args__ = ({"sqlite_autoincrement": True},)

    def __repr__(self):
        return f"<TenantOverride(key={self.flag_key}, tenant_id={self.tenant_id})>"
