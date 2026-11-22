#
//  test_rollback.py
//  
//
//  Created by joechen on 2026/11/22.
//



def test_rollback_creates_new_release_pointing_to_historical_version():
    """
    Given:
      - v1 was previously published
      - v2 is currently active
      - v1's immutable snapshot and artifacts are still available

    When:
      - an authorized release manager requests rollback to v1

    Then:
      - a new Release ID is created
      - the new Release points to v1
      - rollback_of_release_id points to the release being reversed
      - active version changes from v2 to v1
      - the original v2 Release remains unchanged
      - a rollback audit/outbox event is written
    """
    ...


def test_rollback_requires_permission():
    """
    A user without release.rollback permission cannot restore
    a historical version.
    """
    ...


def test_rollback_rejects_missing_or_corrupted_artifact():
    """
    A historical version cannot be restored when its required
    snapshot or release artifact cannot be verified.
    """
    ...
