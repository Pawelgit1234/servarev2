from common.enums import ProtocolType
from pydantic import BaseModel, ConfigDict


class MasscanAddressSchema(BaseModel):  # type: ignore
    protocol: ProtocolType
    port: int
    ip: str
    is_multiport: bool


class PorterSchema(BaseModel):  # type: ignore
    protocol: ProtocolType
    port: int

    model_config = ConfigDict(frozen=True)
