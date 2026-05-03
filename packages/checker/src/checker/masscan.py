from common.enums import ProtocolType
from common.settings import SCANNER_MULTIPORT_IP_SUFFIX
from pydantic import BaseModel


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
