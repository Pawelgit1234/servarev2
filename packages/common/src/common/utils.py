from common.schemas.ip import IpInfoSchema
from common.schemas.server import ServerCheckSchema


def merge_server_check_with_ip_info(
    server: ServerCheckSchema, ip_info: IpInfoSchema
) -> None:
    server.server.country = ip_info.country
    server.server.region = ip_info.region
    server.server.city = ip_info.city
    server.server.latitude = ip_info.latitude
    server.server.longitude = ip_info.longitude
    server.server.hostname = ip_info.hostname
    server.server.asn = ip_info.asn
