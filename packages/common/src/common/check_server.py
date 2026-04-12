import logging

from mcstatus import BedrockServer, JavaServer, LegacyServer

from common.enums import ServerType
from common.schemas.server import ServerSnapshotSchema
from common.settings import SERVER_CHECK_TIMEOUT

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.CRITICAL)

for name in (
    "asyncio",
    "mcstatus",
    "dns",
    "aiosqlite",
):
    logging.getLogger(name).setLevel(logging.CRITICAL)


async def check_java_server(ip: str, port: int) -> ServerSnapshotSchema | None:
    try:
        server = await JavaServer.async_lookup(
            f"{ip}:{port}", SERVER_CHECK_TIMEOUT
        )
        status = await server.async_status()
        # TODO: query
    except Exception:
        return None
    return status


async def check_bedrock_server(
    ip: str, port: int
) -> ServerSnapshotSchema | None:
    try:
        server = BedrockServer.lookup(f"{ip}:{port}", SERVER_CHECK_TIMEOUT)
        status = await server.async_status()
    except Exception:
        return None
    return status


async def check_legacy_server(
    ip: str, port: int
) -> ServerSnapshotSchema | None:
    try:
        server = await LegacyServer.async_lookup(
            f"{ip}:{port}", SERVER_CHECK_TIMEOUT
        )
        status = await server.async_status()
    except Exception:
        return None
    return status


CHECKERS = {
    ServerType.JAVA: check_java_server,
    ServerType.BEDROCK: check_bedrock_server,
    ServerType.LEGACY: check_legacy_server,
}


async def check_server_by_type(
    ip: str, port: int, server_type: ServerType
) -> ServerSnapshotSchema | None:
    checker = CHECKERS[server_type]
    return await checker(ip, port)
