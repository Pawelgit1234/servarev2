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

DISABLE_DOCKER = os.getenv("DISABLE_DOCKER")

if DISABLE_DOCKER is None:
    MULTIPORT_IPS_FILEPATH = "./multiport_ips.txt"
    EXCLUDE_IPS = "./exclude.conf"
    REDIS_HOST = "redis"
else:
    MULTIPORT_IPS_FILEPATH = "./multiport_ips.txt"
    EXCLUDE_IPS = "./exclude.conf"
    # MULTIPORT_IPS_FILEPATH = "./packages/scanner/multiport_ips.txt"
    # EXCLUDE_IPS = "./packages/scanner/exclude.conf"
    REDIS_HOST = "localhost"

SCANNER_ALL_IPS_SUFFIX = "all"
SCANNER_MULTIPORT_IP_SUFFIX = "multiport"

REDIS_IP_QUEUE = "ips"  # scanner -> checker
REDIS_PORTER_QUEUE = "porter"  # checker -> porter

MASSCAN_RATE = get_int("MASSCAN_RATE")
MASSCAN_RATE_TARGET = get_int("MASSCAN_RATE_TARGET")
CHECK_CONCURRENCY = get_int("CHECK_CONCURRENCY")
PORT_CHECK_CONCURRENCY = get_int("PORT_CHECK_CONCURRENCY")
SERVER_CHECK_TIMEOUT = get_int("SERVER_CHECK_TIMEOUT")
AIOHTTP_TIMEOUT = get_int("AIOHTTP_TIMEOUT")
IPINFO_API_TOKEN = os.getenv("IPINFO_API_TOKEN")

S3_ROOT_USER = os.getenv("S3_ROOT_USER")
S3_ROOT_PASSWORD = os.getenv("S3_ROOT_PASSWORD")
S3_BUCKET = "assests"
S3_SKINS_PREFIX = "skins"
S3_CAPES_PREFIX = "capes"
S3_FAVICONS_PREFIX = "favicons"
S3_CHUNK_SECTIONS_PREFIX = "chunk_sections"
S3_ENDPOINT = "http://minio:9000"
S3_GLOBAL_ENDPOINT = "http://localhost:9000"
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
SESSION_URL = "https://sessionserver.mojang.com/session/minecraft/profile/"
PLAYER_SEMAPHORE = 400 // 10  # max 400 requests per 10 seconds
IPINFO_SEMAPHORE = 10
