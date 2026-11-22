//
//  import.swift
//  
//
//  Created by joechen on 2026/11/22.
//



from __future__ import annotations

import hashlib
import json
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class SnapshotError(ValueError):
    pass


VOLATILE_FIELDS = {
    "requestId",
    "correlationId",
    "generatedAt",
    "exportedAt",
    "temporaryPath",
    "runtimeDuration",
}


def _normalize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        value = value.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=False,
        )

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, dict):
        normalized = {}
        for key in sorted(value):
            if key in VOLATILE_FIELDS:
                continue
            normalized[key] = _normalize(value[key])
        return normalized

    if isinstance(value, (list, tuple)):
        # List order is retained because some semantic collections
        # (such as RDF lists) are order-sensitive.
        return [_normalize(item) for item in value]

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    raise SnapshotError(
        f"Unsupported snapshot value type: {type(value).__name__}"
    )


def canonical_snapshot_bytes(snapshot: Any) -> bytes:
    normalized = _normalize(snapshot)

    try:
        text = json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise SnapshotError(f"Cannot serialize snapshot: {exc}") from exc

    return text.encode("utf-8")


def compute_snapshot_hash(snapshot: Any) -> str:
    content = canonical_snapshot_bytes(snapshot)
    return hashlib.sha256(content).hexdigest()


def verify_snapshot_hash(snapshot: Any, expected_hash: str) -> bool:
    actual_hash = compute_snapshot_hash(snapshot)
    return actual_hash == expected_hash
