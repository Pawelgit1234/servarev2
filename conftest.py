import pytest


@pytest.fixture(autouse=True)  # type: ignore
def clean_db() -> None:  # type: ignore
    print("fixture start")
    yield
    print("fixture end")
