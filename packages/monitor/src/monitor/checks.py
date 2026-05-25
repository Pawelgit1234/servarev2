import asyncio

from common.checks.server import (
    check_bedrock_server,
    check_java_server,
    check_legacy_server,
)
from common.enums import ServerType
from common.models.server import ServerModel
from common.schemas.server import ServerCheckSchema
from common.settings import MONITOR_PORT_CONCURRENCY

s = asyncio.Semaphore(MONITOR_PORT_CONCURRENCY)  # type: ignore

CHECKERS = {
    ServerType.JAVA: check_java_server,
    ServerType.BEDROCK: check_bedrock_server,
    ServerType.LEGACY: check_legacy_server,
}


async def check_server_by_type(
    ip: str, port: int, server_type: ServerType
) -> ServerCheckSchema | None:
    async with s:
        checker = CHECKERS[server_type]
        server = await checker(ip, port)
    return server


async def check_servers(
    servers: list[ServerModel],
) -> list[tuple[ServerModel, ServerCheckSchema | None]]:
    results = await asyncio.gather(
        *(check_server_by_type(s.ip, s.port, s.server_type) for s in servers)
    )

    return list(zip(servers, results, strict=True))
