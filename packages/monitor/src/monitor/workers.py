import asyncio
import logging

from common.checks.player import fetch_premium_player_snapshot
from common.databases import async_session
from common.services.common import upload_players, upload_servers
from common.services.entities import load_existing_entities
from common.services.server import (
    create_player_snapshot_if_changed,
    save_servers,
    update_ip_state,
)
from common.settings import DB_RETRY_DELAY_SECONDS
from common.utils import (
    extract_entities_from_checks,
    normalize_player_snapshot,
    normilize_ip,
    restart_on_failure,
)

from monitor.checks import check_servers
from monitor.services import (
    get_next_ip,
    get_next_premium_player,
    prepare_ip_data,
)
from monitor.utils import log_servers_saved, normilize_server_checks

logger = logging.getLogger(__name__)


@restart_on_failure(lambda worker_id: f"player-worker-{worker_id}")  # type: ignore
async def player_worker(worker_id: int) -> None:
    while True:
        async with async_session() as db:  # type: ignore
            # get player
            player = await get_next_premium_player(db)
            if player is None:  # happens only if the database is empty
                logger.warning("Database is empty: no players")
                await asyncio.sleep(DB_RETRY_DELAY_SECONDS)  # type: ignore
                continue

            snapshot_schema = await fetch_premium_player_snapshot(player.uuid)
            if snapshot_schema is None:
                logger.warning("Unsuccessful player request")
                continue

            normalize_player_snapshot(snapshot_schema)
            await upload_players([snapshot_schema])

            create_player_snapshot_if_changed(db, player, snapshot_schema)
            await db.commit()

        logger.info(f"Player {player.uuid} was checked")


@restart_on_failure(lambda worker_id: f"server-worker-{worker_id}")  # type: ignore
async def server_worker(worker_id: int) -> None:
    while True:
        async with async_session() as db:  # type: ignore
            # get ip
            ip = await get_next_ip(db)
            if ip is None:  # happens only if the database is empty
                logger.warning("Database is empty: no servers")
                await asyncio.sleep(DB_RETRY_DELAY_SECONDS)  # type: ignore
                continue

            # ip
            ip_info, update_porter = await prepare_ip_data(ip)
            if ip_info is not None:
                normilize_ip(ip_info)
            update_ip_state(ip, ip_info, update_porter)

            # server
            servers = await check_servers(ip.ip, ip.servers)
            online_server_checks = normilize_server_checks(servers)
            await upload_servers(online_server_checks)

            entities = extract_entities_from_checks(online_server_checks)
            entity_maps = await load_existing_entities(db, entities)

            save_servers(db, servers, entity_maps)
            await db.commit()

        log_servers_saved(ip)
