"""Backward-compatible import for the academic-record CLI wrapper."""

from apps.cli.academic_record_legacy import *  # noqa: F401,F403


if __name__ == "__main__":
    test_hoc_ba_system()
