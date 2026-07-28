from pydantic import BaseModel


class IpInfoSchema(BaseModel):  # type: ignore
    country: str | None = None
    region: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    hostname: str | None = None
    asn: str | None = None
