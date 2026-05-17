import asyncio

from common.checks.ip import get_ip_info
from common.enums import DetectedServiceType, ProtocolType
from common.schemas.server import (
    PorterSchema,
    ServerCheckSchema,
    ServerPortSchema,
)
from common.settings import PORT_CHECK_CONCURRENCY
from common.utils import merge_server_check_with_ip_info

from checker.check import check_server_by_protocol
from checker.detect import detect_service

sem = asyncio.Semaphore(PORT_CHECK_CONCURRENCY)


def parse_porter_address(
    porter_address: str,
) -> tuple[list[PorterSchema], str]:
    # porter tcp:21,22,80|udp:19132,8888 x.x.x.x
    _, ports, ip = porter_address.split()

    port_schemas = []
    for protocol_and_ports in ports.split("|"):
        protocol, ps = protocol_and_ports.split(":")
        for p in ps.split(","):
            if not p:
                continue
            port_schemas.append(PorterSchema(protocol=protocol, port=int(p)))

    return port_schemas, ip


async def limited_check(
    p: PorterSchema, ip: str
) -> ServerPortSchema | ServerCheckSchema:
    async with sem:
        server = await check_server_by_protocol(p.protocol, ip, p.port)
        if server is not None:
            return server

        if p.protocol == ProtocolType.UDP:
            return ServerPortSchema(
                port=p.port,
                protocol_type=ProtocolType.UDP,
                detected_service_type=DetectedServiceType.UNKNOWN,
            )

        return await detect_service(ip, p.port)


async def scan_ports(
    ports: list[PorterSchema], ip: str
) -> tuple[list[ServerPortSchema], list[ServerCheckSchema]]:
    tasks = [limited_check(p, ip) for p in ports]
    results = await asyncio.gather(*tasks)

    server_ports: list[ServerPortSchema] = []
    servers: list[ServerCheckSchema] = []

    for result in results:
        if isinstance(result, ServerCheckSchema):
            servers.append(result)
        else:
            server_ports.append(result)

    return server_ports, servers


async def process_porter(
    ports: list[PorterSchema], ip: str
) -> tuple[list[ServerPortSchema], list[ServerCheckSchema]]:
    ports, servers = await scan_ports(ports, ip)

    ip_info = await get_ip_info(ip)
    for server in servers:
        merge_server_check_with_ip_info(server, ip_info)

    return ports, servers
