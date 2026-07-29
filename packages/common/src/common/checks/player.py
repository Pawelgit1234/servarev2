import asyncio
import base64
import json
import uuid

from aiohttp import ClientError
from common.enums import PlayerType
from common.schemas.player import PlayerSchema, PlayerSnapshotSchema
from common.session import session_manager
from common.settings import MOJANG_SEMAPHORE, SESSION_URL
from common.utils import retry_on_none
from mcstatus.responses import JavaStatusPlayer

s = asyncio.Semaphore(MOJANG_SEMAPHORE)

# No need, because status already includes uuids
#
# async def fetch_uuids(names: list[str]) -> dict[str, str]:
#     async with session.post(MOJANG_BULK_URL, json=names) as resp:
#         data = await resp.json()
#
#     return {item["name"]: item["id"] for item in data}


def normalize_uuid_dashed(u: str) -> str | None:
    try:
        return str(uuid.UUID(u))
    except ValueError:
        return None


def is_offline_uuid(name: str, u: str) -> bool:
    expected = uuid.uuid3(uuid.NAMESPACE_DNS, f"OfflinePlayer:{name}")
    return str(expected) == str(uuid.UUID(u))


@retry_on_none()  # type: ignore
async def fetch_premium_player_snapshot(u: str) -> PlayerSnapshotSchema | None:
    """Use only if you sure that this player exists in Mojang api"""

    try:
        async with (
            s,
            session_manager.session.get(f"{SESSION_URL}/{u}") as resp,
        ):
            if resp.status != 200:
                return None

            data = await resp.json()

    except (TimeoutError, ClientError):
        return None

    properties = data.get("properties", [])
    name = data["name"]
    skin = cape = None

    if properties:
        value = properties[0].get("value")
        if value:
            decoded = json.loads(base64.b64decode(value))
            textures = decoded.get("textures", {})

            skin = textures.get("SKIN", {}).get("url")
            cape = textures.get("CAPE", {}).get("url")

    return PlayerSnapshotSchema(
        name=name,
        skin=skin,
        cape=cape,
    )


async def fetch_profile(
    name: str, uuid_raw: str
) -> tuple[PlayerSchema, PlayerSnapshotSchema]:
    u = normalize_uuid_dashed(uuid_raw)

    if u is None:
        return (
            PlayerSchema(uuid=uuid_raw, player_type=PlayerType.OFFLINE),
            PlayerSnapshotSchema(name=name, skin=None, cape=None),
        )

    offline = (
        PlayerSchema(uuid=u, player_type=PlayerType.OFFLINE),
        PlayerSnapshotSchema(name=name, skin=None, cape=None),
    )

    if name.startswith((".", "*")):  # geyser/floodgate
        return (
            PlayerSchema(uuid=u, player_type=PlayerType.BEDROCK),
            PlayerSnapshotSchema(name=name, skin=None, cape=None),
        )

    if is_offline_uuid(name, u):
        return offline

    try:
        async with (
            s,
            session_manager.session.get(f"{SESSION_URL}/{u}") as resp,
        ):
            if resp.status != 200:
                return offline

            data = await resp.json()
    except (TimeoutError, ClientError):
        return offline

    if data["name"].lower() != name.lower():
        return offline

    properties = data.get("properties", [])
    skin = cape = None

    if properties:
        value = properties[0].get("value")
        if value:
            decoded = json.loads(base64.b64decode(value))
            textures = decoded.get("textures", {})

            skin = textures.get("SKIN", {}).get("url")
            cape = textures.get("CAPE", {}).get("url")

    return (
        PlayerSchema(uuid=u, player_type=PlayerType.PREMIUM),
        PlayerSnapshotSchema(name=name, skin=skin, cape=cape),
    )


async def download_by_url(url: str) -> bytes | None:
    try:
        async with s, session_manager.session.get(url) as resp:
            if resp.status != 200:
                return None
            return await resp.read()  # type: ignore
    except Exception:
        return None


async def fetch_players(
    players: list[JavaStatusPlayer],
) -> dict[PlayerSchema, PlayerSnapshotSchema]:
    tasks = [fetch_profile(p.name, p.uuid) for p in players]
    results = await asyncio.gather(*tasks)

    return {player: snapshot for player, snapshot in results}
