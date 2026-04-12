from enum import Enum

from pydantic import BaseModel, Field, IPvAnyAddress


class ProtocolType(Enum):
    TCP = "tcp"
    UDP = "udp"


class MasscanAddressSchema(BaseModel):
    protocol: ProtocolType
    port: int = Field(ge=0, le=65535)
    ip: IPvAnyAddress


def parse_masscan_address(masscan_address: str) -> MasscanAddressSchema:
    """Parses masscan output address"""

    #   0   1    2      3        4
    # open tcp 25565 x.x.x.x 1775807568

    m = masscan_address.split()
    return MasscanAddressSchema(protocol=m[1], ip=m[3], port=int(m[2]))  # type: ignore


# async def check_server_by_masscan(
#     masscan: MasscanAddressSchema,
# ) -> ServerResponse | None:
#     if masscan.protocol == ProtocolType.TCP:
#         return await (
#             check_java_server(masscan.ip, masscan.port)
#             or check_legacy_server(masscan.ip, masscan.port)
#         )
#
#     if masscan.protocol == ProtocolType.UDP:
#         return await check_bedrock_server(masscan.ip, masscan.port)
#
#     return None
#
