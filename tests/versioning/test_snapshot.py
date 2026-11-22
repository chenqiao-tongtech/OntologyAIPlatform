#
//  test_snapshot.py
//  
//
//  Created by joechen on 2026/11/22.
//



from ontology.versioning.snapshot import (
    compute_snapshot_hash,
    verify_snapshot_hash,
)


def test_snapshot_hash_ignores_object_key_order():
    first = {
        "ontologyId": "ontology-001",
        "classes": [
            {"id": "class-001", "iri": "https://example.org/Customer"}
        ],
    }

    second = {
        "classes": [
            {"iri": "https://example.org/Customer", "id": "class-001"}
        ],
        "ontologyId": "ontology-001",
    }

    assert compute_snapshot_hash(first) == compute_snapshot_hash(second)


def test_snapshot_hash_changes_when_semantics_change():
    first = {
        "classes": [
            {"id": "class-001", "iri": "https://example.org/Customer"}
        ]
    }
    second = {
        "classes": [
            {"id": "class-001", "iri": "https://example.org/Client"}
        ]
    }

    assert compute_snapshot_hash(first) != compute_snapshot_hash(second)


def test_snapshot_hash_verification():
    snapshot = {
        "ontologyId": "ontology-001",
        "version": "1.0.0",
    }

    digest = compute_snapshot_hash(snapshot)

    assert verify_snapshot_hash(snapshot, digest)
    assert not verify_snapshot_hash(
        {"ontologyId": "ontology-001", "version": "1.0.1"},
        digest,
    )
