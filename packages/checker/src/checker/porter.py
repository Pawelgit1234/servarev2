import asyncio

from common.enums import ProtocolType
from common.schemas.server import ServerCheckSchema
from common.settings import PORT_CHECK_CONCURRENCY
from pydantic import BaseModel, ConfigDict

from checker.check import check_server_by_protocol

sem = asyncio.Semaphore(PORT_CHECK_CONCURRENCY)


class PorterSchema(BaseModel):
    protocol: ProtocolType
    port: int

    model_config = ConfigDict(frozen=True)


def parse_porter_address(
    porter_address: str,
) -> tuple[list[PorterSchema], str]:
    # porter tcp:21,22,80,|udp:19132,8888, x.x.x.x
    _, ports, ip = porter_address.split()

    port_schemas = []
    for protocol_and_ports in ports.split("|"):
        protocol, ps = protocol_and_ports.split(":")
        for p in ps.split(","):
            if not p:
                continue
            port_schemas.append(PorterSchema(protocol=protocol, port=int(p)))

    return port_schemas, ip


async def limited_check(p: PorterSchema, ip: str) -> ServerCheckSchema | None:
    async with sem:
        return await check_server_by_protocol(p.protocol, ip, p.port)


async def scan_ports(
    ports: list[PorterSchema], ip: str
) -> dict[PorterSchema, ServerCheckSchema | None]:
    tasks = {p: limited_check(p, ip) for p in ports}
    results = await asyncio.gather(*tasks.values())
    return {key: result for key, result in zip(tasks.keys(), results)}  # noqa: B905
