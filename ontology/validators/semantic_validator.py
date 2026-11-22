"""Semantic consistency checks for P1 ontology snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ontology.metamodel.identifiers import ensure_absolute_iri


@dataclass(frozen=True)
class SemanticIssue:
    code: str
    severity: str
    path: str
    message: str
    target_id: str | None = None


@dataclass(frozen=True)
class SemanticValidationReport:
    valid: bool
    issues: tuple[SemanticIssue, ...]

    @property
    def errors(self) -> tuple[SemanticIssue, ...]:
        return tuple(item for item in self.issues if item.severity == "error")

    @property
    def warnings(self) -> tuple[SemanticIssue, ...]:
        return tuple(item for item in self.issues if item.severity == "warning")


def _get(item: Mapping[str, Any], camel: str, snake: str | None = None, default=None):
    if camel in item:
        return item[camel]
    if snake and snake in item:
        return item[snake]
    return default


def _id(item: Mapping[str, Any]) -> str:
    value = _get(item, "id")
    return str(value).lower() if value is not None else ""


class SemanticValidator:
    """Validates IRI uniqueness, class hierarchy and property semantics."""

    def validate(self, snapshot: Mapping[str, Any]) -> SemanticValidationReport:
        issues: list[SemanticIssue] = []
        groups = {
            "classes": _get(snapshot, "classes", default=[]) or [],
            "datatypeProperties": _get(snapshot, "datatypeProperties", "datatype_properties", []) or [],
            "objectProperties": _get(snapshot, "objectProperties", "object_properties", []) or [],
            "relations": _get(snapshot, "relations", default=[]) or [],
            "terms": _get(snapshot, "terms", default=[]) or [],
        }

        iri_owners: dict[str, tuple[str, str]] = {}
        for group_name in ("classes", "datatypeProperties", "objectProperties", "terms"):
            for index, item in enumerate(groups[group_name]):
                iri = _get(item, "iri")
                if not iri:
                    continue
                path = f"$.{group_name}[{index}].iri"
                try:
                    ensure_absolute_iri(str(iri))
                except ValueError as exc:
                    issues.append(
                        SemanticIssue(
                            "INVALID_IRI", "error", path, str(exc), _id(item) or None
                        )
                    )
                    continue
                normalized = str(iri)
                if normalized in iri_owners:
                    previous_group, previous_id = iri_owners[normalized]
                    issues.append(
                        SemanticIssue(
                            "DUPLICATE_IRI",
                            "error",
                            path,
                            f"IRI is already used by {previous_group} object {previous_id}.",
                            _id(item) or None,
                        )
                    )
                else:
                    iri_owners[normalized] = (group_name, _id(item))

        class_by_id = {
            _id(item): item for item in groups["classes"] if _id(item)
        }
        datatype_by_id = {
            _id(item): item for item in groups["datatypeProperties"] if _id(item)
        }
        object_by_id = {
            _id(item): item for item in groups["objectProperties"] if _id(item)
        }

        # Check class parent references and detect inheritance cycles.
        graph: dict[str, list[str]] = {}
        for index, item in enumerate(groups["classes"]):
            current_id = _id(item)
            parents = [
                str(value).lower()
                for value in (_get(item, "parentClassIds", "parent_class_ids", []) or [])
            ]
            graph[current_id] = parents
            for parent_id in parents:
                if parent_id not in class_by_id:
                    issues.append(
                        SemanticIssue(
                            "UNKNOWN_PARENT_CLASS",
                            "error",
                            f"$.classes[{index}].parentClassIds",
                            f"Parent class {parent_id} does not exist.",
                            current_id or None,
                        )
                    )

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str, stack: list[str]) -> None:
            if node in visiting:
                cycle = " -> ".join(stack + [node])
                issues.append(
                    SemanticIssue(
                        "CLASS_HIERARCHY_CYCLE",
                        "error",
                        "$.classes",
                        f"Class hierarchy contains a cycle: {cycle}.",
                        node,
                    )
                )
                return
            if node in visited:
                return
            visiting.add(node)
            for parent in graph.get(node, []):
                if parent in graph:
                    visit(parent, stack + [node])
            visiting.remove(node)
            visited.add(node)

        for class_id in graph:
            visit(class_id, [])

        # Validate data property domains and cardinality.
        for index, prop in enumerate(groups["datatypeProperties"]):
            path = f"$.datatypeProperties[{index}]"
            domains = _get(prop, "domainClassIds", "domain_class_ids", []) or []
            if not domains:
                issues.append(
                    SemanticIssue(
                        "EMPTY_DATATYPE_DOMAIN",
                        "error",
                        path,
                        "DatatypeProperty must have at least one domain class.",
                        _id(prop) or None,
                    )
                )
            for domain_id in domains:
                if str(domain_id).lower() not in class_by_id:
                    issues.append(
                        SemanticIssue(
                            "UNKNOWN_DATATYPE_DOMAIN",
                            "error",
                            f"{path}.domainClassIds",
                            f"Domain class {domain_id} does not exist.",
                            _id(prop) or None,
                        )
                    )
            minimum = _get(prop, "minCount", "min_count")
            maximum = _get(prop, "maxCount", "max_count")
            if minimum is not None and maximum is not None and minimum > maximum:
                issues.append(
                    SemanticIssue(
                        "INVALID_CARDINALITY",
                        "error",
                        path,
                        "minCount cannot exceed maxCount.",
                        _id(prop) or None,
                    )
                )
            datatype_iri = _get(prop, "datatypeIri", "datatype_iri")
            if datatype_iri:
                try:
                    ensure_absolute_iri(str(datatype_iri))
                except ValueError as exc:
                    issues.append(
                        SemanticIssue(
                            "INVALID_DATATYPE_IRI",
                            "error",
                            f"{path}.datatypeIri",
                            str(exc),
                            _id(prop) or None,
                        )
                    )

        # Validate object property domain and range.
        for index, prop in enumerate(groups["objectProperties"]):
            path = f"$.objectProperties[{index}]"
            for field_name, snake_name in (
                ("domainClassIds", "domain_class_ids"),
                ("rangeClassIds", "range_class_ids"),
            ):
                refs = _get(prop, field_name, snake_name, []) or []
                if not refs:
                    issues.append(
                        SemanticIssue(
                            "EMPTY_PROPERTY_ENDPOINT",
                            "error",
                            f"{path}.{field_name}",
                            f"{field_name} must contain at least one class.",
                            _id(prop) or None,
                        )
                    )
                for ref in refs:
                    if str(ref).lower() not in class_by_id:
                        issues.append(
                            SemanticIssue(
                                "UNKNOWN_PROPERTY_ENDPOINT",
                                "error",
                                f"{path}.{field_name}",
                                f"Class {ref} does not exist.",
                                _id(prop) or None,
                            )
                        )

        # Relation is a view/mapping over exactly one ObjectProperty.
        for index, relation in enumerate(groups["relations"]):
            path = f"$.relations[{index}]"
            prop_id = str(
                _get(relation, "objectPropertyId", "object_property_id", "")
            ).lower()
            prop = object_by_id.get(prop_id)
            if prop is None:
                continue
            source_id = str(
                _get(relation, "sourceClassId", "source_class_id", "")
            ).lower()
            target_id = str(
                _get(relation, "targetClassId", "target_class_id", "")
            ).lower()
            domains = {
                str(value).lower()
                for value in _get(prop, "domainClassIds", "domain_class_ids", []) or []
            }
            ranges = {
                str(value).lower()
                for value in _get(prop, "rangeClassIds", "range_class_ids", []) or []
            }
            if source_id not in domains:
                issues.append(
                    SemanticIssue(
                        "RELATION_DOMAIN_MISMATCH",
                        "error",
                        path,
                        "Relation source class is outside the ObjectProperty domain.",
                        _id(relation) or None,
                    )
                )
            if target_id not in ranges:
                issues.append(
                    SemanticIssue(
                        "RELATION_RANGE_MISMATCH",
                        "error",
                        path,
                        "Relation target class is outside the ObjectProperty range.",
                        _id(relation) or None,
                    )
                )

        return SemanticValidationReport(
            valid=not any(issue.severity == "error" for issue in issues),
            issues=tuple(issues),
        )

    def assert_valid(self, snapshot: Mapping[str, Any]) -> None:
        report = self.validate(snapshot)
        if not report.valid:
            detail = "; ".join(
                f"{item.path}: {item.message}" for item in report.errors
            )
            raise ValueError(detail)
