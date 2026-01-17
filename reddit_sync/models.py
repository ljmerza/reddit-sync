"""Data models for Reddit Sync."""

from dataclasses import dataclass, field


@dataclass
class Multireddit:
    """A Reddit multireddit (custom feed)."""

    name: str
    subreddits: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {"name": self.name, "subreddits": self.subreddits}

    @classmethod
    def from_dict(cls, data: dict) -> "Multireddit":
        """Create from dict (JSON deserialization)."""
        return cls(name=data["name"], subreddits=data.get("subreddits", []))


@dataclass
class MultiUpdate:
    """Represents changes needed to update an existing multireddit."""

    name: str
    add: list[str] = field(default_factory=list)
    remove: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {"name": self.name, "add": self.add, "remove": self.remove}


@dataclass
class AccountData:
    """Data exported from a Reddit account."""

    username: str
    subreddits: list[str] = field(default_factory=list)
    multireddits: list[Multireddit] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "source_account": self.username,
            "subreddits": self.subreddits,
            "multireddits": [m.to_dict() for m in self.multireddits],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AccountData":
        """Create from dict (JSON deserialization)."""
        return cls(
            username=data.get("source_account", "unknown"),
            subreddits=data.get("subreddits", []),
            multireddits=[Multireddit.from_dict(m) for m in data.get("multireddits", [])],
        )


@dataclass
class SyncDiff:
    """Differences between source and target accounts."""

    subs_to_add: list[str] = field(default_factory=list)
    subs_to_remove: list[str] = field(default_factory=list)
    multis_to_add: list[Multireddit] = field(default_factory=list)
    multis_to_remove: list[Multireddit] = field(default_factory=list)
    multis_to_update: list[MultiUpdate] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "subs_to_add": self.subs_to_add,
            "subs_to_remove": self.subs_to_remove,
            "multis_to_add": [m.to_dict() for m in self.multis_to_add],
            "multis_to_remove": [m.to_dict() for m in self.multis_to_remove],
            "multis_to_update": [m.to_dict() for m in self.multis_to_update],
        }

    def has_changes(self) -> bool:
        """Check if there are any differences."""
        return bool(
            self.subs_to_add
            or self.subs_to_remove
            or self.multis_to_add
            or self.multis_to_remove
            or self.multis_to_update
        )
