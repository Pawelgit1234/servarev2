from common.checks.server import (
    check_bedrock_server,
    check_java_server,
    check_legacy_server,
)
from common.enums import ProtocolType
from common.schemas.server import ServerCheckSchema


async def check_server_by_protocol(
    protocol: ProtocolType, ip: str, port: int
) -> ServerCheckSchema | None:
    if protocol == ProtocolType.TCP:
        for fn in (check_java_server, check_legacy_server):
            result = await fn(ip, port)
            if result:
                return result

    elif protocol == ProtocolType.UDP:
        return await check_bedrock_server(ip, port)

    return None
