#
//  test_release_service.py
//  
//
//  Created by joechen on 2026/11/22.
//



def test_publish_updates_active_version_only_after_artifacts_ready():
    """
    Given:
      - a validated immutable ontology version
      - an active version pointer referencing v1
      - an artifact builder that returns valid artifacts

    When:
      - ReleaseService publishes v2 with expected_active_version=v1

    Then:
      - all artifacts are stored and hash-verified
      - a Release record is created
      - active version becomes v2
      - an outbox event is written in the same database transaction
    """
    # Implement with FakeVersionRepository, FakeArtifactBuilder,
    # FakeImmutableArtifactStore and FakeUnitOfWork.
    ...


def test_publish_failure_keeps_previous_active_version():
    """
    Artifact generation or database commit failure must leave the
    active version pointer unchanged.
    """
    ...


def test_publish_is_idempotent():
    """
    Repeating the same idempotency key with the same payload returns
    the existing Release record and does not create a second release.
    """
    ...


def test_same_idempotency_key_with_different_payload_is_rejected():
    """
    The same key cannot publish a different version or environment.
    """
    ...
