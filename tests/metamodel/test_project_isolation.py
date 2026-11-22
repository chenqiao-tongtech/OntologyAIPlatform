from uuid import uuid4

from ontology.validators.reference_validator import ReferenceValidator


def test_cross_project_element_is_rejected():
    project_a = str(uuid4())
    project_b = str(uuid4())
    ontology_id = str(uuid4())
    version_id = str(uuid4())
    class_a = str(uuid4())
    class_b = str(uuid4())

    snapshot = {
        "id": version_id,
        "projectId": project_a,
        "ontologyId": ontology_id,
        "classes": [
            {
                "id": class_a,
                "projectId": project_a,
                "ontologyId": ontology_id,
                "ontologyVersionId": version_id,
                "parentClassIds": [],
            },
            {
                "id": class_b,
                "projectId": project_b,
                "ontologyId": ontology_id,
                "ontologyVersionId": version_id,
                "parentClassIds": [class_a],
            },
        ],
        "datatypeProperties": [],
        "objectProperties": [],
        "relations": [],
        "constraints": [],
        "terms": [],
    }

    issues = ReferenceValidator().validate_snapshot(snapshot)
    assert any(issue.code == "CROSS_PROJECT_OBJECT" for issue in issues)
