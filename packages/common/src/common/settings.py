import os


def get_int(name: str) -> None | int:
    env = os.getenv(name)
    if env is not None:
        return int(env)
    return env


DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DB_USERNAME')}:"
    f"{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

REDIS_PORT = 6379

IS_NETWORK_MODE_HOST = os.getenv("IS_NETWORK_MODE_HOST")

REDIS_HOST = "redis" if IS_NETWORK_MODE_HOST is None else "localhost"

MULTIPORT_IPS_FILEPATH = "./multiport_ips.txt"
EXCLUDE_IPS = "./exclude.conf"
SCANNER_ALL_IPS_SUFFIX = "all"
SCANNER_MULTIPORT_IP_SUFFIX = "multiport"

REDIS_IP_QUEUE = "ips"  # scanner -> checker
REDIS_PORTER_QUEUE = "porter"  # checker -> porter

DEEP_CHECK_INTERVAL_DAYS = get_int("DEEP_CHECK_INTERVAL_DAYS")
MASSCAN_RATE = get_int("MASSCAN_RATE")
MASSCAN_RATE_TARGET = get_int("MASSCAN_RATE_TARGET")
CHECK_CONCURRENCY = get_int("CHECK_CONCURRENCY")
PORT_CHECK_CONCURRENCY = get_int("PORT_CHECK_CONCURRENCY")
PORTER_BATCH_SIZE = get_int("PORTER_BATCH_SIZE")
SERVER_CHECK_TIMEOUT = get_int("SERVER_CHECK_TIMEOUT")
AIOHTTP_TIMEOUT = get_int("AIOHTTP_TIMEOUT")
IPINFO_API_TOKEN = os.getenv("IPINFO_API_TOKEN")

S3_ROOT_USER = os.getenv("S3_ROOT_USER")
S3_ROOT_PASSWORD = os.getenv("S3_ROOT_PASSWORD")
S3_BUCKET = "assests"
S3_SKIN_PREFIX = "skins"
S3_CAPE_PREFIX = "capes"
S3_ICON_PREFIX = "icons"
S3_SUBCHUNK_PREFIX = "subchunks"
S3_ENDPOINT = "http://minio:9000"
S3_PUBLIC_ENDPOINT = os.getenv("S3_PUBLIC_ENDPOINT")
S3_PUBLIC_READ_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{S3_BUCKET}/*"],
        }
    ],
}

MOJANG_BULK_URL = "https://api.mojang.com/profiles/minecraft"
SESSION_URL = "https://sessionserver.mojang.com/session/minecraft/profile"
MOJANG_SEMAPHORE = 400 // 10  # max 400 requests per 10 seconds
IPINFO_SEMAPHORE = 8
