"""Cross-object references, ownership and project-isolation validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ReferenceIssue:
    code: str
    path: str
    message: str


class ReferenceValidationError(ValueError):
    def __init__(self, issues: tuple[ReferenceIssue, ...]):
        self.issues = issues
        super().__init__("; ".join(f"{item.path}: {item.message}" for item in issues))


def _get(item: Mapping[str, Any], camel: str, snake: str | None = None, default=None):
    if camel in item:
        return item[camel]
    if snake and snake in item:
        return item[snake]
    return default


def _key(value: Any) -> str:
    return str(value).lower() if value is not None else ""


class ReferenceValidator:
    """Validates references within a complete ontology-version snapshot."""

    def validate_snapshot(self, snapshot: Mapping[str, Any]) -> tuple[ReferenceIssue, ...]:
        issues: list[ReferenceIssue] = []
        project_id = _key(_get(snapshot, "projectId", "project_id"))
        ontology_id = _key(_get(snapshot, "ontologyId", "ontology_id"))
        version_id = _key(_get(snapshot, "id"))
        groups = {
            "classes": _get(snapshot, "classes", default=[]) or [],
            "datatypeProperties": _get(snapshot, "datatypeProperties", "datatype_properties", []) or [],
            "objectProperties": _get(snapshot, "objectProperties", "object_properties", []) or [],
            "relations": _get(snapshot, "relations", default=[]) or [],
            "constraints": _get(snapshot, "constraints", default=[]) or [],
            "terms": _get(snapshot, "terms", default=[]) or [],
        }

        objects: dict[str, tuple[str, Mapping[str, Any], str]] = {}
        for group_name, items in groups.items():
            for index, item in enumerate(items):
                object_id = _key(_get(item, "id"))
                path = f"$.{group_name}[{index}]"
                if not object_id:
                    issues.append(ReferenceIssue("MISSING_ID", path, "Object ID is required."))
                    continue
                if object_id in objects:
                    issues.append(
                        ReferenceIssue("DUPLICATE_ID", f"{path}.id", "Duplicate ID in snapshot.")
                    )
                else:
                    objects[object_id] = (group_name, item, path)

                item_project = _key(_get(item, "projectId", "project_id"))
                if item_project and item_project != project_id:
                    issues.append(
                        ReferenceIssue(
                            "CROSS_PROJECT_OBJECT",
                            f"{path}.projectId",
                            "Snapshot object belongs to a different project.",
                        )
                    )
                item_ontology = _key(_get(item, "ontologyId", "ontology_id"))
                if item_ontology and ontology_id and item_ontology != ontology_id:
                    issues.append(
                        ReferenceIssue(
                            "CROSS_ONTOLOGY_OBJECT",
                            f"{path}.ontologyId",
                            "Snapshot object belongs to a different ontology.",
                        )
                    )
                item_version = _key(
                    _get(item, "ontologyVersionId", "ontology_version_id")
                )
                if item_version and version_id and item_version != version_id:
                    issues.append(
                        ReferenceIssue(
                            "CROSS_VERSION_OBJECT",
                            f"{path}.ontologyVersionId",
                            "Snapshot object belongs to a different version.",
                        )
                    )

        class_ids = {
            _key(_get(item, "id"))
            for item in groups["classes"]
            if _get(item, "id") is not None
        }
        datatype_by_id = {
            _key(_get(item, "id")): item
            for item in groups["datatypeProperties"]
            if _get(item, "id") is not None
        }
        object_property_by_id = {
            _key(_get(item, "id")): item
            for item in groups["objectProperties"]
            if _get(item, "id") is not None
        }

        for index, item in enumerate(groups["classes"]):
            path = f"$.classes[{index}]"
            for parent_id in _get(item, "parentClassIds", "parent_class_ids", []) or []:
                if _key(parent_id) not in class_ids:
                    issues.append(
                        ReferenceIssue(
                            "UNRESOLVED_PARENT_CLASS",
                            f"{path}.parentClassIds",
                            f"Parent class {parent_id!s} is not in this snapshot.",
                        )
                    )
                elif _key(parent_id) == _key(_get(item, "id")):
                    issues.append(
                        ReferenceIssue(
                            "SELF_PARENT",
                            f"{path}.parentClassIds",
                            "A class cannot be its own parent.",
                        )
                    )

        for group_name in ("datatypeProperties", "objectProperties"):
            for index, item in enumerate(groups[group_name]):
                path = f"$.{group_name}[{index}]"
                for field_name, snake_name in (
                    ("domainClassIds", "domain_class_ids"),
                    ("rangeClassIds", "range_class_ids"),
                ):
                    refs = _get(item, field_name, snake_name, None)
                    if refs is None and group_name == "datatypeProperties" and field_name == "rangeClassIds":
                        continue
                    for ref_id in refs or []:
                        if _key(ref_id) not in class_ids:
                            issues.append(
                                ReferenceIssue(
                                    "UNRESOLVED_CLASS_REFERENCE",
                                    f"{path}.{field_name}",
                                    f"Referenced class {ref_id!s} is not in this snapshot.",
                                )
                            )

        for index, relation in enumerate(groups["relations"]):
            path = f"$.relations[{index}]"
            source_id = _key(_get(relation, "sourceClassId", "source_class_id"))
            target_id = _key(_get(relation, "targetClassId", "target_class_id"))
            property_id = _key(_get(relation, "objectPropertyId", "object_property_id"))

            if source_id not in class_ids:
                issues.append(
                    ReferenceIssue("UNRESOLVED_RELATION_SOURCE", path, "Source class is missing.")
                )
            if target_id not in class_ids:
                issues.append(
                    ReferenceIssue("UNRESOLVED_RELATION_TARGET", path, "Target class is missing.")
                )
            prop = object_property_by_id.get(property_id)
            if prop is None:
                issues.append(
                    ReferenceIssue(
                        "UNRESOLVED_OBJECT_PROPERTY",
                        f"{path}.objectPropertyId",
                        "Relation ObjectProperty is missing.",
                    )
                )
            else:
                domain_ids = {
                    _key(item)
                    for item in _get(prop, "domainClassIds", "domain_class_ids", []) or []
                }
                range_ids = {
                    _key(item)
                    for item in _get(prop, "rangeClassIds", "range_class_ids", []) or []
                }
                if source_id not in domain_ids:
                    issues.append(
                        ReferenceIssue(
                            "RELATION_DOMAIN_MISMATCH",
                            path,
                            "Relation source class is not in the ObjectProperty domain.",
                        )
                    )
                if target_id not in range_ids:
                    issues.append(
                        ReferenceIssue(
                            "RELATION_RANGE_MISMATCH",
                            path,
                            "Relation target class is not in the ObjectProperty range.",
                        )
                    )

        for index, constraint in enumerate(groups["constraints"]):
            path = f"$.constraints[{index}]"
            target_id = _key(_get(constraint, "targetId", "target_id"))
            if target_id and target_id not in objects:
                issues.append(
                    ReferenceIssue(
                        "UNRESOLVED_CONSTRAINT_TARGET",
                        f"{path}.targetId",
                        "Constraint target is not present in this snapshot.",
                    )
                )

        return tuple(issues)

    def assert_snapshot_valid(self, snapshot: Mapping[str, Any]) -> None:
        issues = self.validate_snapshot(snapshot)
        if issues:
            raise ReferenceValidationError(issues)
