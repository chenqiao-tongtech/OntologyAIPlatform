"""Schema-version migration and compatibility validation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable

from ontology.metamodel.identifiers import compare_semver, parse_semver
from ontology.validators.schema_validator import SchemaValidator


Migration = Callable[[dict[str, Any]], dict[str, Any]]


class CompatibilityError(ValueError):
    pass


@dataclass(frozen=True)
class CompatibilityResult:
    document: dict[str, Any]
    source_version: str
    target_version: str
    migrated: bool
    migration_path: tuple[tuple[str, str], ...]


class SchemaCompatibilityValidator:
    """Applies explicitly registered migrations to a target schema version.

    Migrations are one-way functions. Downgrades are rejected. The validator
    never silently guesses how to transform an unknown or breaking schema.
    """

    def __init__(
        self,
        target_version: str,
        schema_validator: SchemaValidator,
        target_schema_name: str,
    ):
        parse_semver(target_version)
        self.target_version = target_version
        self.schema_validator = schema_validator
        self.target_schema_name = target_schema_name
        self._migrations: dict[tuple[str, str], Migration] = {}

    def register_migration(
        self,
        source_version: str,
        target_version: str,
        migration: Migration,
    ) -> None:
        parse_semver(source_version)
        parse_semver(target_version)
        if compare_semver(source_version, target_version) >= 0:
            raise CompatibilityError("Migration target must be newer than source.")
        key = (source_version, target_version)
        if key in self._migrations:
            raise CompatibilityError(f"Migration already registered: {key}")
        self._migrations[key] = migration

    def migrate(
        self,
        document: dict[str, Any],
        source_version: str,
    ) -> CompatibilityResult:
        parse_semver(source_version)
        if compare_semver(source_version, self.target_version) > 0:
            raise CompatibilityError("Schema downgrade is not supported.")

        output = deepcopy(document)
        if source_version == self.target_version:
            self.schema_validator.validate_or_raise(
                output, self.target_schema_name
            )
            return CompatibilityResult(
                output,
                source_version,
                self.target_version,
                False,
                (),
            )

        path = self._find_path(source_version, self.target_version)
        if path is None:
            raise CompatibilityError(
                f"No registered migration path from {source_version} "
                f"to {self.target_version}."
            )

        for source, target in path:
            output = self._migrations[(source, target)](output)
            if not isinstance(output, dict):
                raise CompatibilityError("Migration must return a JSON object.")
            output["schemaVersion"] = target

        self.schema_validator.validate_or_raise(
            output, self.target_schema_name
        )
        return CompatibilityResult(
            output,
            source_version,
            self.target_version,
            True,
            tuple(path),
        )

    def _find_path(
        self,
        source_version: str,
        target_version: str,
    ) -> list[tuple[str, str]] | None:
        queue: list[tuple[str, list[tuple[str, str]]]] = [(source_version, [])]
        visited = {source_version}
        while queue:
            current, path = queue.pop(0)
            if current == target_version:
                return path
            for edge in sorted(self._migrations):
                edge_source, edge_target = edge
                if edge_source != current or edge_target in visited:
                    continue
                if compare_semver(edge_target, target_version) > 0:
                    continue
                visited.add(edge_target)
                queue.append((edge_target, path + [edge]))
        return None
