from common.settings import SCANNER_MULTIPORT_IP_SUFFIX

from checker.schemas import MasscanAddressSchema, PorterSchema


def parse_masscan_address(masscan_address: str) -> MasscanAddressSchema:
    """Parses masscan output address"""

    #   0   1    2      3        4          5
    # open tcp 25565 x.x.x.x 1775807568 multiport/all

    _, p, port, ip, _, m = masscan_address.split()
    return MasscanAddressSchema(
        protocol=p,  # type: ignore
        port=int(port),
        ip=ip,
        is_multiport=m == SCANNER_MULTIPORT_IP_SUFFIX,
    )


def parse_porter_address(
    porter_address: str,
) -> tuple[list[PorterSchema], str]:
    # tcp:21,22,80|udp:19132,8888 x.x.x.x
    ports, ip = porter_address.split()

    port_schemas = []
    for protocol_and_ports in ports.split("|"):
        protocol, ps = protocol_and_ports.split(":")
        for p in ps.split(","):
            if not p:
                continue
            port_schemas.append(PorterSchema(protocol=protocol, port=int(p)))  # type: ignore

    return port_schemas, ip
