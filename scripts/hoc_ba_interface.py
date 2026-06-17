"""Backward-compatible import for the academic-record CLI."""

from apps.cli.academic_record import *  # noqa: F401,F403


if __name__ == "__main__":
    goi_y_hoc_ba_main()
