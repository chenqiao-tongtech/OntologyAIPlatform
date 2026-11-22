//
//  SemanticDiffService.swift
//  
//
//  Created by joechen on 2026/11/22.
//



from __future__ import annotations

import json
from typing import Any, Mapping

from ontology.versioning.models import (
    Compatibility,
    ImpactLevel,
    SemanticChange,
    SemanticDiffReport,
)


COLLECTIONS = {
    "classes": "class",
    "datatypeProperties": "datatype_property",
    "objectProperties": "object_property",
    "relations": "relation",
    "constraints": "constraint",
    "terms": "term",
    "semanticAxioms": "semantic_axiom",
    "opaqueConstructs": "opaque_construct",
}


def _value(obj: Mapping[str, Any], camel: str, snake: str | None = None):
    if camel in obj:
        return obj[camel]
    if snake is not None and snake in obj:
        return obj[snake]
    return None


def _identity(obj: Mapping[str, Any]) -> str:
    # Stable internal ID is preferred. IRI is a controlled fallback
    # for imported constructs that do not yet have a persistent ID.
    value = _value(obj, "id")
    if value is None:
        value = _value(obj, "iri")
    if value is None:
        raise ValueError("Semantic object must have id or iri.")
    return str(value)


def _semantic_value(value: Any) -> Any:
    if isinstance(value, dict):
        ignored = {
            "updatedAt", "updated_at",
            "createdAt", "created_at",
            "updatedBy", "updated_by",
        }
        return {
            key: _semantic_value(item)
            for key, item in sorted(value.items())
            if key not in ignored
        }

    if isinstance(value, list):
        return [_semantic_value(item) for item in value]

    return value


def _object_map(items: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    result = {}
    for item in items:
        key = _identity(item)
        if key in result:
            raise ValueError(f"Duplicate object identity in snapshot: {key}")
        result[key] = item
    return result


class SemanticDiffService:
    """Compare two immutable OIR snapshot payloads."""

    def compare(
        self,
        old_snapshot: Mapping[str, Any],
        new_snapshot: Mapping[str, Any],
        old_version: str | None = None,
        new_version: str | None = None,
    ) -> SemanticDiffReport:
        changes: list[SemanticChange] = []

        for collection, object_type in COLLECTIONS.items():
            old_items = old_snapshot.get(collection, []) or []
            new_items = new_snapshot.get(collection, []) or []

            old_map = _object_map(old_items)
            new_map = _object_map(new_items)

            for key in sorted(old_map.keys() - new_map.keys()):
                item = old_map[key]
                changes.append(
                    self._removed(object_type, item)
                )

            for key in sorted(new_map.keys() - old_map.keys()):
                item = new_map[key]
                changes.append(
                    self._added(object_type, item)
                )

            for key in sorted(old_map.keys() & new_map.keys()):
                old_item = old_map[key]
                new_item = new_map[key]
                changes.extend(
                    self._changed(object_type, old_item, new_item)
                )

        # Namespace changes affect external IRIs and should be visible.
        old_namespace = old_snapshot.get("namespace")
        new_namespace = new_snapshot.get("namespace")
        if old_namespace != new_namespace:
            changes.append(
                SemanticChange(
                    change_type="namespace_changed",
                    target_type="ontology",
                    target_id=str(old_snapshot.get("ontologyId", "")) or None,
                    target_iri=str(old_namespace) if old_namespace else None,
                    impact=ImpactLevel.HIGH,
                    compatibility=Compatibility.BREAKING,
                    migration_required=True,
                    rationale="Ontology namespace changed; dependent IRIs may require migration.",
                    old_value=old_namespace,
                    new_value=new_namespace,
                )
            )

        return SemanticDiffReport(
            source_version=old_version,
            target_version=new_version,
            changes=tuple(changes),
        )

    def _added(self, object_type: str, item: Mapping[str, Any]) -> SemanticChange:
        if object_type in {"semantic_axiom", "opaque_construct"}:
            compatibility = Compatibility.UNKNOWN
            impact = ImpactLevel.MEDIUM
            rationale = (
                "A new logical or opaque construct was added; "
                "compatibility requires semantic inspection."
            )
        elif object_type == "constraint":
            compatibility = Compatibility.CONDITIONALLY_COMPATIBLE
            impact = ImpactLevel.MEDIUM
            rationale = (
                "A new constraint may reject existing data; "
                "run validation against dependent datasets."
            )
        else:
            compatibility = Compatibility.COMPATIBLE
            impact = ImpactLevel.LOW
            rationale = "A new semantic object was added."

        return SemanticChange(
            change_type=f"{object_type}_added",
            target_type=object_type,
            target_id=str(item.get("id")) if item.get("id") else None,
            target_iri=item.get("iri"),
            impact=impact,
            compatibility=compatibility,
            migration_required=False,
            rationale=rationale,
            new_value=_semantic_value(dict(item)),
        )

    def _removed(self, object_type: str, item: Mapping[str, Any]) -> SemanticChange:
        return SemanticChange(
            change_type=f"{object_type}_removed",
            target_type=object_type,
            target_id=str(item.get("id")) if item.get("id") else None,
            target_iri=item.get("iri"),
            impact=ImpactLevel.HIGH,
            compatibility=Compatibility.BREAKING,
            migration_required=True,
            rationale=(
                "Removing a semantic object may invalidate references, "
                "mappings, constraints or dependent applications."
            ),
            old_value=_semantic_value(dict(item)),
        )

    def _changed(
        self,
        object_type: str,
        old_item: Mapping[str, Any],
        new_item: Mapping[str, Any],
    ) -> list[SemanticChange]:
        result: list[SemanticChange] = []
        old = _semantic_value(dict(old_item))
        new = _semantic_value(dict(new_item))

        target_id = str(new_item.get("id") or old_item.get("id") or "")
        target_iri = new_item.get("iri") or old_item.get("iri")

        # IRI changes are semantically important even when internal ID stays stable.
        if old_item.get("iri") != new_item.get("iri"):
            result.append(
                SemanticChange(
                    change_type=f"{object_type}_iri_changed",
                    target_type=object_type,
                    target_id=target_id or None,
                    target_iri=target_iri,
                    impact=ImpactLevel.HIGH,
                    compatibility=Compatibility.BREAKING,
                    migration_required=True,
                    rationale="Semantic IRI changed; external references may need migration.",
                    old_value=old_item.get("iri"),
                    new_value=new_item.get("iri"),
                )
            )

        if object_type == "class":
            self._compare_field(
                result, object_type, target_id, target_iri,
                old_item, new_item,
                "parentClassIds", "parent_class_ids",
                "class_hierarchy_changed",
                ImpactLevel.HIGH,
                Compatibility.CONDITIONALLY_COMPATIBLE,
                True,
                "Class hierarchy changed and may alter inferred types.",
            )

        elif object_type == "datatype_property":
            self._compare_field(
                result, object_type, target_id, target_iri,
                old_item, new_item,
                "datatypeIri", "datatype_iri",
                "datatype_changed",
                ImpactLevel.HIGH,
                Compatibility.BREAKING,
                True,
                "Changing a datatype may invalidate data mappings and consumers.",
            )
            for field in ("domainClassIds", "domain_class_ids"):
                if field in old_item or field in new_item:
                    break
            self._compare_field(
                result, object_type, target_id, target_iri,
                old_item, new_item,
                "domainClassIds", "domain_class_ids",
                "property_domain_changed",
                ImpactLevel.HIGH,
                Compatibility.CONDITIONALLY_COMPATIBLE,
                True,
                "DatatypeProperty domain changed.",
            )
            self._compare_field(
                result, object_type, target_id, target_iri,
                old_item, new_item,
                "minCount", "min_count",
                "minimum_cardinality_changed",
                ImpactLevel.HIGH,
                Compatibility.CONDITIONALLY_COMPATIBLE,
                True,
                "Minimum cardinality changes may invalidate existing data.",
            )
            self._compare_field(
                result, object_type, target_id, target_iri,
                old_item, new_item,
                "maxCount", "max_count",
                "maximum_cardinality_changed",
                ImpactLevel.MEDIUM,
                Compatibility.CONDITIONALLY_COMPATIBLE,
                True,
                "Maximum cardinality changes may affect data validation.",
            )

        elif object_type == "object_property":
            for field in ("domainClassIds", "rangeClassIds"):
                self._compare_field(
                    result, object_type, target_id, target_iri,
                    old_item, new_item,
                    field, self._snake(field),
                    f"{field[0].lower()}{field[1:]}_changed",
                    ImpactLevel.HIGH,
                    Compatibility.CONDITIONALLY_COMPATIBLE,
                    True,
                    f"ObjectProperty {field} changed.",
                )
            self._compare_field(
                result, object_type, target_id, target_iri,
                old_item, new_item,
                "characteristics", None,
                "property_characteristics_changed",
                ImpactLevel.HIGH,
                Compatibility.UNKNOWN,
                True,
                "OWL property characteristics changed; logical impact requires review.",
            )

        elif object_type == "constraint":
            if old != new:
                result.append(
                    SemanticChange(
                        change_type="constraint_changed",
                        target_type=object_type,
                        target_id=target_id or None,
                        target_iri=target_iri,
                        impact=ImpactLevel.HIGH,
                        compatibility=Compatibility.CONDITIONALLY_COMPATIBLE,
                        migration_required=True,
                        rationale="Constraint expression changed; dependent data must be revalidated.",
                        old_value=old,
                        new_value=new,
                    )
                )

        elif object_type in {"semantic_axiom", "opaque_construct"}:
            if old != new:
                result.append(
                    SemanticChange(
                        change_type=f"{object_type}_changed",
                        target_type=object_type,
                        target_id=target_id or None,
                        target_iri=target_iri,
                        impact=ImpactLevel.HIGH,
                        compatibility=Compatibility.UNKNOWN,
                        migration_required=True,
                        rationale="Logical or opaque construct changed; compatibility is not inferred automatically.",
                        old_value=old,
                        new_value=new,
                    )
                )

        else:
            # Labels, definitions, aliases and other metadata may still be
            # semantically relevant; report the change without overclaiming.
            if old != new:
                result.append(
                    SemanticChange(
                        change_type=f"{object_type}_modified",
                        target_type=object_type,
                        target_id=target_id or None,
                        target_iri=target_iri,
                        impact=ImpactLevel.LOW,
                        compatibility=Compatibility.CONDITIONALLY_COMPATIBLE,
                        migration_required=False,
                        rationale="Object metadata changed; review language and consumer expectations.",
                        old_value=old,
                        new_value=new,
                    )
                )

        return result

    @staticmethod
    def _snake(camel: str) -> str:
        import re
        return re.sub(r"(?<!^)(?=[A-Z])", "_", camel).lower()

    @staticmethod
    def _compare_field(
        output: list[SemanticChange],
        object_type: str,
        target_id: str,
        target_iri: str | None,
        old_item: Mapping[str, Any],
        new_item: Mapping[str, Any],
        camel: str,
        snake: str | None,
        change_type: str,
        impact: ImpactLevel,
        compatibility: Compatibility,
        migration_required: bool,
        rationale: str,
    ) -> None:
        old_value = _value(old_item, camel, snake)
        new_value = _value(new_item, camel, snake)
        if old_value == new_value:
            return

        output.append(
            SemanticChange(
                change_type=change_type,
                target_type=object_type,
                target_id=target_id or None,
                target_iri=target_iri,
                impact=impact,
                compatibility=compatibility,
                migration_required=migration_required,
                rationale=rationale,
                old_value=old_value,
                new_value=new_value,
            )
        )
