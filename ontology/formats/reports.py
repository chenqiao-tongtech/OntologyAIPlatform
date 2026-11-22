//
//  import.swift
//  
//
//  Created by joechen on 2026/11/21.
//



from dataclasses import dataclass, field
from enum import Enum


class MappingStatus(str, Enum):
    EXACT = "exact"
    NORMALIZED = "normalized"
    PRESERVED = "preserved"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ConversionIssue:
    code: str
    status: MappingStatus
    source_location: str | None
    message: str
    construct_type: str | None = None


@dataclass
class ConversionReport:
    operation_id: str
    source_format: str | None = None
    target_format: str | None = None
    mapped_construct_count: int = 0
    normalized_construct_count: int = 0
    preserved_construct_count: int = 0
    unsupported_construct_count: int = 0
    issues: list[ConversionIssue] = field(default_factory=list)

    @property
    def has_blocking_issues(self) -> bool:
        return any(
            item.status == MappingStatus.UNSUPPORTED
            for item in self.issues
        )

    def add(self, issue: ConversionIssue) -> None:
        self.issues.append(issue)
        if issue.status == MappingStatus.EXACT:
            self.mapped_construct_count += 1
        elif issue.status == MappingStatus.NORMALIZED:
            self.normalized_construct_count += 1
        elif issue.status == MappingStatus.PRESERVED:
            self.preserved_construct_count += 1
        elif issue.status == MappingStatus.UNSUPPORTED:
            self.unsupported_construct_count += 1
