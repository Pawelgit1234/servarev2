import asyncio

from common.checks.server import (
    check_bedrock_server,
    check_java_server,
    check_legacy_server,
)
from common.enums import ServerType
from common.models.server import ServerModel
from common.schemas.server import ServerCheckSchema

CHECKERS = {
    ServerType.JAVA: check_java_server,
    ServerType.BEDROCK: check_bedrock_server,
    ServerType.LEGACY: check_legacy_server,
}


async def check_server_by_type(
    ip: str, port: int, server_type: ServerType
) -> ServerCheckSchema | None:
    checker = CHECKERS[server_type]
    server = await checker(ip, port)
    return server


async def check_servers(
    ip: str, servers: list[ServerModel]
) -> list[tuple[ServerModel, ServerCheckSchema | None]]:
    results = await asyncio.gather(
        *(check_server_by_type(ip, s.port, s.server_type) for s in servers)
    )

    return list(zip(servers, results, strict=True))
