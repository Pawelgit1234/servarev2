from enum import Enum

from common.checks.server import (
    check_bedrock_server,
    check_java_server,
    check_legacy_server,
)
from common.schemas.server import ServerCheckSchema
from pydantic import BaseModel


class ProtocolType(Enum):
    TCP = "tcp"
    UDP = "udp"


class MasscanAddressSchema(BaseModel):
    protocol: ProtocolType
    port: int
    ip: str


def parse_masscan_address(masscan_address: str) -> MasscanAddressSchema:
    """Parses masscan output address"""

    #   0   1    2      3        4
    # open tcp 25565 x.x.x.x 1775807568

    m = masscan_address.split()
    return MasscanAddressSchema(protocol=m[1], ip=m[3], port=int(m[2]))  # type: ignore


async def check_server_by_masscan(
    masscan: MasscanAddressSchema,
) -> ServerCheckSchema | None:
    if masscan.protocol == ProtocolType.TCP:
        for fn in (check_java_server, check_legacy_server):
            result = await fn(masscan.ip, masscan.port)
            if result:
                return result

    if masscan.protocol == ProtocolType.UDP:
        return await check_bedrock_server(masscan.ip, masscan.port)

    return None
