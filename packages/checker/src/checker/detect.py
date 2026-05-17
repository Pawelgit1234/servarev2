from aiohttp import ClientError
from common.enums import DetectedServiceType, ProtocolType
from common.schemas.server import ServerPortSchema
from common.session import session_manager

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
) -> ServerPortSchema:
    """Detects HTTP-based services."""

    url = f"http://{ip}:{port}"

    try:
        async with session_manager.session.get(
            url,
            allow_redirects=True,
        ) as resp:
            text = await resp.text(errors="ignore")

    except (TimeoutError, ClientError):
        return ServerPortSchema(
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

    return ServerPortSchema(
        port=port,
        protocol_type=ProtocolType.TCP,
        detected_service_type=detected,
    )
