from checker.parsers import parse_masscan_address, parse_porter_address
from checker.schemas import MasscanAddressSchema, PorterSchema
from common.enums import ProtocolType


def test_parse_masscan_address() -> None:
    address = "open tcp 25565 0.0.0.0 1775807568 all"
    masscan = parse_masscan_address(address)
    assert masscan == MasscanAddressSchema(
        protocol=ProtocolType.TCP, port=25565, ip="0.0.0.0", is_multiport=False
    )


def test_parse_porter_address() -> None:
    address = "tcp:22,80|udp:19132 0.0.0.0"
    ports, ip = parse_porter_address(address)

    assert ip == "0.0.0.0"
    assert ports == [
        PorterSchema(protocol=ProtocolType.TCP, port=22),
        PorterSchema(protocol=ProtocolType.TCP, port=80),
        PorterSchema(protocol=ProtocolType.UDP, port=19132),
    ]
