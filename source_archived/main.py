"""
[ARCHIVED] Script entry point — legacy prototype v0.

Original exploration script for wiring up the DBManager. Most of the
body was commented out during development and was never finalised.

Status
------
Superseded by ``backend/app/main.py`` and ``run.sh``.

This file is kept for historical reference only. Do not run it.
"""

from source_archived.db_manager import DBManager


def main() -> None:
    """
    Prototype entry point (incomplete).

    Originally intended to instantiate DBManager and load documents
    from a local PDF directory. The body was commented out during
    development and never completed.

    For the current entry point see ``backend/app/main.py``.
    """
    # Example usage (paths must be updated for your environment):
    #
    # data_path = "/path/to/pdf/directory"
    # db_path   = "/path/to/vector/db"
    # manager   = DBManager(data_path, db_path, chunk_size=500, chunk_overlap=50)
    # manager.load_documents()


if __name__ == "__main__":
    main()
