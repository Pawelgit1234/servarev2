import pytest
from common.checks.server import is_lan


@pytest.mark.parametrize(
    ("players_online", "players_max", "motd", "expected"),
    [
        # Valid LAN servers
        (
            1,
            8,
            "Nichname - Survival",
            True,
        ),
        (
            5,
            8,
            "My LAN Server - Modded",
            True,
        ),
        # Invalid because no separator
        (
            1,
            8,
            "Steve's World",
            False,
        ),
        # Invalid because wrong max players
        (
            1,
            20,
            "Steve's World - Survival",
            False,
        ),
        # Invalid because no online players
        (
            0,
            8,
            "Steve's World - Survival",
            False,
        ),
        # Valid with underscores and spaces
        (
            3,
            8,
            "My_Server 1 - SMP",
            True,
        ),
    ],
)
def test_is_lan(
    players_online: int,
    players_max: int,
    motd: str,
    expected: bool,
) -> None:
    assert is_lan(players_online, players_max, motd) is expected
