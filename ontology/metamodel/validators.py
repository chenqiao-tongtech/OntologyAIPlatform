//
//  MetaModelReferenceError.swift
//  
//
//  Created by joechen on 2026/11/21.
//



from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from ontology.metamodel.models import (
    OntologyClass,
    ObjectProperty,
    Relation,
)


class MetaModelReferenceError(ValueError):
    """Raised when an ontology snapshot contains invalid references."""


def validate_class_references(
    project_id: UUID,
    classes: list[OntologyClass],
) -> None:
    """
    Validate class identity and parent references within one project
    and one ontology snapshot.
    """
    class_by_id = {item.id: item for item in classes}

    if len(class_by_id) != len(classes):
        raise MetaModelReferenceError("Duplicate class IDs found.")

    for item in classes:
        if item.project_id != project_id:
            raise MetaModelReferenceError(
                f"Class {item.id} belongs to another project."
            )

        for parent_id in item.parent_class_ids:
            parent = class_by_id.get(parent_id)

            if parent is None:
                raise MetaModelReferenceError(
                    f"Parent class {parent_id} does not exist "
                    f"in the current ontology snapshot."
                )

            if parent.project_id != item.project_id:
                raise MetaModelReferenceError(
                    "Cross-project class reference is not allowed."
                )

            if parent.id == item.id:
                raise MetaModelReferenceError(
                    "A class cannot be its own direct parent."
                )


def validate_object_property_references(
    project_id: UUID,
    classes: list[OntologyClass],
    properties: list[ObjectProperty],
) -> None:
    class_by_id = {item.id: item for item in classes}

    property_ids = [item.id for item in properties]
    if len(property_ids) != len(set(property_ids)):
        raise MetaModelReferenceError(
            "Duplicate object property IDs found."
        )

    for prop in properties:
        if prop.project_id != project_id:
            raise MetaModelReferenceError(
                f"ObjectProperty {prop.id} belongs to another project."
            )

        for class_id in (
            prop.domain_class_ids + prop.range_class_ids
        ):
            target = class_by_id.get(class_id)

            if target is None:
                raise MetaModelReferenceError(
                    f"Referenced class {class_id} does not exist "
                    f"in the current snapshot."
                )

            if target.project_id != prop.project_id:
                raise MetaModelReferenceError(
                    "Cross-project property reference is not allowed."
                )


def validate_relation_references(
    project_id: UUID,
    classes: list[OntologyClass],
    properties: list[ObjectProperty],
    relations: list[Relation],
) -> None:
    class_ids = {item.id for item in classes}
    property_by_id = {item.id: item for item in properties}

    relation_ids = [item.id for item in relations]
    if len(relation_ids) != len(set(relation_ids)):
        raise MetaModelReferenceError("Duplicate relation IDs found.")

    for relation in relations:
        if relation.project_id != project_id:
            raise MetaModelReferenceError(
                "Relation belongs to another project."
            )

        if relation.source_class_id not in class_ids:
            raise MetaModelReferenceError(
                "Relation source class does not exist."
            )

        if relation.target_class_id not in class_ids:
            raise MetaModelReferenceError(
                "Relation target class does not exist."
            )

        prop = property_by_id.get(relation.object_property_id)
        if prop is None:
            raise MetaModelReferenceError(
                "Relation ObjectProperty does not exist."
            )

        if relation.source_class_id not in prop.domain_class_ids:
            raise MetaModelReferenceError(
                "Relation source is not included in ObjectProperty domain."
            )

        if relation.target_class_id not in prop.range_class_ids:
            raise MetaModelReferenceError(
                "Relation target is not included in ObjectProperty range."
            )
