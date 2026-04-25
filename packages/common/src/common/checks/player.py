import asyncio
import base64
import json

import aiohttp
from common.enums import PlayerType
from common.schemas.player import PlayerSchema, PlayerSnapshotSchema
from common.settings import PLAYER_SEMAPHORE_COUNT, SESSION_URL
from mcstatus.responses import JavaStatusPlayer

SEMAPHORE = asyncio.Semaphore(PLAYER_SEMAPHORE_COUNT)

# No need, because status already includes uuids
#
# async def fetch_uuids(
#     session: aiohttp.ClientSession, names: list[str]
# ) -> dict[str, str]:
#     async with session.post(MOJANG_BULK_URL, json=names) as resp:
#         data = await resp.json()
#
#     return {item["name"]: item["id"] for item in data}


async def fetch_profile(
    session: aiohttp.ClientSession, name: str, uuid: str
) -> tuple[PlayerSchema, PlayerSnapshotSchema]:
    async with SEMAPHORE, session.get(f"{SESSION_URL}{uuid}") as resp:
        if resp.status != 200:
            player = PlayerSchema(
                uuid=uuid,
                player_type=PlayerType.OFFLINE,
            )
            snapshot = PlayerSnapshotSchema(
                name=name,
                skin=None,
                cape=None,
            )
            return player, snapshot

        data = await resp.json()

    if data["name"].lower() != name.lower():
        player = PlayerSchema(
            uuid=uuid,
            player_type=PlayerType.OFFLINE,
        )
        snapshot = PlayerSnapshotSchema(
            name=name,
            skin=None,
            cape=None,
        )
        return player, snapshot

    textures = data["properties"][0]["value"]
    decoded = json.loads(base64.b64decode(textures))

    skin = decoded["textures"].get("SKIN", {}).get("url")
    cape = decoded["textures"].get("CAPE", {}).get("url")

    player = PlayerSchema(
        uuid=uuid,
        player_type=PlayerType.PREMIUM,
    )
    snapshot = PlayerSnapshotSchema(
        name=name,
        skin=skin,
        cape=cape,
    )

    return player, snapshot


async def fetch_players(
    players: list[JavaStatusPlayer],
) -> dict[PlayerSchema, PlayerSnapshotSchema]:
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_profile(session, p.name, p.uuid) for p in players]
        results = await asyncio.gather(*tasks)

    return {player: snapshot for player, snapshot in results}
