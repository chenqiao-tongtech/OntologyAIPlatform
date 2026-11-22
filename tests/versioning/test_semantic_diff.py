#
//  test_semantic_diff.py
//  
//
//  Created by joechen on 2026/11/22.
//



from ontology.versioning.models import Compatibility
from ontology.versioning.semantic_diff import SemanticDiffService


def test_added_class_is_detected():
    old = {"classes": []}
    new = {
        "classes": [
            {
                "id": "class-001",
                "iri": "https://example.org/Customer",
                "preferredLabels": [
                    {"value": "Customer", "language": "en"}
                ],
            }
        ]
    }

    report = SemanticDiffService().compare(old, new)

    assert len(report.changes) == 1
    assert report.changes[0].change_type == "class_added"
    assert report.changes[0].compatibility == Compatibility.COMPATIBLE


def test_removed_class_is_breaking():
    old = {
        "classes": [
            {
                "id": "class-001",
                "iri": "https://example.org/Customer",
            }
        ]
    }
    new = {"classes": []}

    report = SemanticDiffService().compare(old, new)

    assert report.has_breaking_changes
    assert report.changes[0].change_type == "class_removed"


def test_datatype_change_is_breaking():
    old = {
        "datatypeProperties": [
            {
                "id": "prop-001",
                "iri": "https://example.org/customerId",
                "datatypeIri": "http://www.w3.org/2001/XMLSchema#string",
            }
        ]
    }
    new = {
        "datatypeProperties": [
            {
                "id": "prop-001",
                "iri": "https://example.org/customerId",
                "datatypeIri": "http://www.w3.org/2001/XMLSchema#integer",
            }
        ]
    }

    report = SemanticDiffService().compare(old, new)

    assert any(
        item.change_type == "datatype_changed"
        and item.compatibility == Compatibility.BREAKING
        for item in report.changes
    )


def test_iri_change_is_detected_even_when_internal_id_is_stable():
    old = {
        "classes": [
            {
                "id": "class-001",
                "iri": "https://example.org/Customer",
            }
        ]
    }
    new = {
        "classes": [
            {
                "id": "class-001",
                "iri": "https://example.org/Client",
            }
        ]
    }

    report = SemanticDiffService().compare(old, new)

    assert any(
        item.change_type == "class_iri_changed"
        for item in report.changes
    )


def test_new_constraint_requires_compatibility_review():
    old = {"constraints": []}
    new = {
        "constraints": [
            {
                "id": "constraint-001",
                "engine": "shacl",
                "expression": "minCount 1",
            }
        ]
    }

    report = SemanticDiffService().compare(old, new)

    assert report.changes[0].compatibility == (
        Compatibility.CONDITIONALLY_COMPATIBLE
    )
