import asyncio

from aiohttp import ClientError
from common.schemas.ip import IpInfoSchema
from common.session import session_manager
from common.settings import IPINFO_API_TOKEN, IPINFO_SEMAPHORE

s = asyncio.Semaphore(IPINFO_SEMAPHORE)


async def get_ip_info(ip: str) -> IpInfoSchema:
    url = f"https://ipinfo.io/{ip}/json?token={IPINFO_API_TOKEN}"

    try:
        async with s, session_manager.session.get(url) as resp:
            if resp.status != 200:
                return IpInfoSchema()

            data = await resp.json()
    except (TimeoutError, ClientError):
        return IpInfoSchema()

    loc = data.get("loc")
    lat, lon = (None, None)

    if loc:
        try:  # noqa: SIM105
            lat, lon = map(float, loc.split(","))
        except Exception:
            pass

    return IpInfoSchema(
        country=data.get("country"),
        region=data.get("region"),
        city=data.get("city"),
        latitude=lat,
        longitude=lon,
        hostname=data.get("hostname"),
        asn=data.get("org"),
    )
