from __future__ import annotations

import pytest

from consent_lab.logging_setup import clear_redactions, reset_logging


@pytest.fixture(autouse=True)
def _reset_logging() -> object:
    reset_logging()
    clear_redactions()
    yield
    reset_logging()
    clear_redactions()
