import asyncio

from aiohttp import ClientError
from common.checks.server import (
    check_bedrock_server,
    check_java_server,
    check_legacy_server,
)
from common.enums import DetectedServiceType, ProtocolType
from common.schemas.server import IpPortSchema, ServerCheckSchema
from common.session import session_manager
from common.settings import CHECKER_PORT_CONCURRENCY

from checker.schemas import PorterSchema

s = asyncio.Semaphore(CHECKER_PORT_CONCURRENCY)  # type: ignore


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


SIGNATURES: dict[DetectedServiceType, list[str]] = {
    # Maps
    DetectedServiceType.BLUEMAP: [
        "bluemap",
    ],
    DetectedServiceType.DYNMAP: ["dynmap", "dynamic"],
    DetectedServiceType.PL3XMAP: [
        "pl3xmap",
    ],
    DetectedServiceType.SQUAREMAP: [
        "squaremap",
    ],
    # Panels
    DetectedServiceType.PTERODACTYL: [
        "pterodactyl",
    ],
    DetectedServiceType.PELICAN: [
        "pelican panel",
        "pelican",
    ],
    DetectedServiceType.AMP: [
        "cubecoders amp",
        "amp",
        "application management panel",
    ],
    DetectedServiceType.MULTICRAFT: [
        "multicraft",
    ],
    DetectedServiceType.CRAFTY: [
        "crafty controller",
        "crafty",
    ],
}


async def detect_service(
    ip: str,
    port: int,
) -> IpPortSchema:
    """Detects HTTP-based services."""

    url = f"http://{ip}:{port}"

    try:
        async with session_manager.session.get(
            url,
            allow_redirects=True,
        ) as resp:
            text = await resp.text(errors="ignore")

    except (TimeoutError, ClientError):
        return IpPortSchema(
            port=port,
            protocol_type=ProtocolType.TCP,
            detected_service_type=DetectedServiceType.UNKNOWN,
        )

    body = text.lower()

    detected = DetectedServiceType.GENERIC_HTTP

    for service_type, signatures in SIGNATURES.items():
        if any(signature in body for signature in signatures):
            detected = service_type
            break

    return IpPortSchema(
        port=port,
        protocol_type=ProtocolType.TCP,
        detected_service_type=detected,
    )


async def limited_check(
    p: PorterSchema, ip: str
) -> IpPortSchema | ServerCheckSchema:
    async with s:
        server = await check_server_by_protocol(p.protocol, ip, p.port)
        if server is not None:
            return server

        if p.protocol == ProtocolType.UDP:
            return IpPortSchema(
                port=p.port,
                protocol_type=ProtocolType.UDP,
                detected_service_type=DetectedServiceType.UNKNOWN,
            )

        return await detect_service(ip, p.port)


async def check_server_ports(
    ports: list[PorterSchema], ip: str
) -> tuple[list[IpPortSchema], list[ServerCheckSchema]]:
    tasks = [limited_check(p, ip) for p in ports]
    results = await asyncio.gather(*tasks)

    server_ports: list[IpPortSchema] = []
    servers: list[ServerCheckSchema] = []

    for result in results:
        if isinstance(result, ServerCheckSchema):
            servers.append(result)
        else:
            server_ports.append(result)

    return server_ports, servers
