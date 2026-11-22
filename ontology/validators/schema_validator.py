"""JSON Schema Draft 2020-12 registry and validation service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from ontology.metamodel.identifiers import ensure_absolute_iri


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str
    schema_path: str | None = None


@dataclass(frozen=True)
class SchemaValidationReport:
    schema_name: str
    valid: bool
    issues: tuple[ValidationIssue, ...]

    def raise_for_errors(self) -> None:
        if not self.valid:
            summary = "; ".join(
                f"{issue.path}: {issue.message}" for issue in self.issues
            )
            raise SchemaValidationError(summary)


class SchemaValidationError(ValueError):
    pass


class SchemaRegistryError(RuntimeError):
    pass


class SchemaValidator:
    """Loads all schemas into a local registry and validates payloads.

    No remote schema fetching is performed. All $ref targets must be present
    in the configured schema directory or be local fragment references.
    """

    def __init__(self, schema_dir: str | Path):
        self.schema_dir = Path(schema_dir)
        self.schemas: dict[str, dict[str, Any]] = {}
        self._registry = Registry()
        self._format_checker = FormatChecker()
        self._format_checker.checks("iri")(self._is_iri)
        self._load_all()

    @staticmethod
    def _is_iri(value: str) -> bool:
        try:
            ensure_absolute_iri(value)
            return True
        except (TypeError, ValueError):
            return False

    def _load_all(self) -> None:
        if not self.schema_dir.is_dir():
            raise SchemaRegistryError(f"Schema directory not found: {self.schema_dir}")

        for path in sorted(self.schema_dir.glob("*.schema.json")):
            try:
                schema = json.loads(path.read_text(encoding="utf-8"))
                Draft202012Validator.check_schema(schema)
            except Exception as exc:
                raise SchemaRegistryError(f"Invalid schema file {path}: {exc}") from exc

            name = path.name.removesuffix(".schema.json")
            if name in self.schemas:
                raise SchemaRegistryError(f"Duplicate schema name: {name}")
            self.schemas[name] = schema

        for schema in self.schemas.values():
            schema_id = schema.get("$id")
            if not schema_id:
                raise SchemaRegistryError("Every schema must declare a stable $id.")
            self._registry = self._registry.with_resource(
                schema_id,
                Resource.from_contents(schema),
            )

    def list_schemas(self) -> tuple[str, ...]:
        return tuple(sorted(self.schemas))

    def check_schema(self, schema_name: str) -> None:
        schema = self._get_schema(schema_name)
        Draft202012Validator.check_schema(schema)

    def validate(
        self,
        payload: Any,
        schema_name: str,
    ) -> SchemaValidationReport:
        schema = self._get_schema(schema_name)
        validator = Draft202012Validator(
            schema,
            registry=self._registry,
            format_checker=self._format_checker,
        )
        errors = sorted(
            validator.iter_errors(payload),
            key=lambda error: (
                list(error.absolute_path),
                error.message,
            ),
        )
        issues = tuple(
            ValidationIssue(
                code="SCHEMA_VALIDATION_ERROR",
                path="$" + "".join(
                    f"[{part}]" if isinstance(part, int) else f".{part}"
                    for part in error.absolute_path
                ),
                message=error.message,
                schema_path="#" + "/".join(str(part) for part in error.absolute_schema_path),
            )
            for error in errors
        )
        return SchemaValidationReport(
            schema_name=schema_name,
            valid=not issues,
            issues=issues,
        )

    def validate_or_raise(self, payload: Any, schema_name: str) -> None:
        self.validate(payload, schema_name).raise_for_errors()

    def _get_schema(self, schema_name: str) -> dict[str, Any]:
        try:
            return self.schemas[schema_name]
        except KeyError as exc:
            raise SchemaRegistryError(
                f"Unknown schema {schema_name!r}; available: {self.list_schemas()}"
            ) from exc
