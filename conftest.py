import pytest


@pytest.fixture(autouse=True)  # type: ignore
def clean_db() -> None:  # type: ignore
    yield
