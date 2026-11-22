#
//  conftest.py
//  
//
//  Created by joechen on 2026/11/21.
//


import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def class_schema():
    schema_path = (
        ROOT
        / "ontology"
        / "schemas"
        / "class.schema.json"
    )

    with schema_path.open("r", encoding="utf-8") as file:
        return json.load(file)