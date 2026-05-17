from common.checks.ip import get_ip_info
from common.enums import ProtocolType
from common.schemas.server import ServerCheckSchema
from common.settings import SCANNER_MULTIPORT_IP_SUFFIX
from common.utils import merge_server_check_with_ip_info
from pydantic import BaseModel

from checker.check import check_server_by_protocol


class MasscanAddressSchema(BaseModel):
    protocol: ProtocolType
    port: int
    ip: str
    is_multiport: bool


def parse_masscan_address(masscan_address: str) -> MasscanAddressSchema:
    """Parses masscan output address"""

    #   0   1    2      3        4          5
    # open tcp 25565 x.x.x.x 1775807568 multiport/all

    _, p, port, ip, _, m = masscan_address.split()
    return MasscanAddressSchema(
        protocol=p,
        port=int(port),
        ip=ip,
        is_multiport=m == SCANNER_MULTIPORT_IP_SUFFIX,
    )


async def process_masscan(
    masscan: MasscanAddressSchema,
) -> ServerCheckSchema | None:
    server = await check_server_by_protocol(
        masscan.protocol, masscan.ip, masscan.port
    )
    if server is None:
        return None

    server.server.is_multiport = masscan.is_multiport

    ip_info = await get_ip_info(masscan.ip)
    merge_server_check_with_ip_info(server, ip_info)
    return server
