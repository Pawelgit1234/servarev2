import os


def get_int(name: str) -> int | None:
    env = os.getenv(name)
    if env is not None:
        return int(env)
    return env


DB_URL = (
    f"postgresql+asyncpg://{os.getenv('DB_USERNAME')}:"
    f"{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
DB_POOL_SIZE = get_int("DB_POOL_SIZE")
DB_MAX_OVERFLOW = get_int("DB_MAX_OVERFLOW")
DB_POOL_TIMEOUT = get_int("DB_POOL_TIMEOUT")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

MULTIPORT_IPS_FILEPATH = "./multiport_ips.txt"
EXCLUDE_IPS = "./exclude.conf"
SCANNER_ALL_IPS_SUFFIX = "all"
SCANNER_MULTIPORT_IP_SUFFIX = "multiport"

REDIS_IP_QUEUE = "ips"  # scanner -> checker
REDIS_PORTER_QUEUE = "porter"  # checker -> porter

DB_RETRY_DELAY_SECONDS = get_int("DB_RETRY_DELAY_SECONDS")

COUNTRY_MAX = 2
REGION_MAX = 100
CITY_MAX = 100
HOSTNAME_MAX = 255
ASN_MAX = 150
SERVER_VERSION_MAX = 32
SERVER_MOTD_MAX = 512
SERVER_MAP_NAME_MAX = 64
SERVER_GAMEMODE_MAX = 32
USERNAME_MAX = 16
SOFTWARE_VERSION_MAX = 32
RESOURCE_PACK_URL_MAX = 512
PLUGIN_NAME_MAX = 128
MOD_NAME_MAX = 128
MOD_VERSION_MAX = 32


IP_CHECK_INTERVAL_DAYS = get_int("IP_CHECK_INTERVAL_DAYS")
PORTER_CHECK_INTERVAL_DAYS = get_int("PORTER_CHECK_INTERVAL_DAYS")
MASSCAN_RATE = get_int("MASSCAN_RATE")
MASSCAN_RATE_TARGET = get_int("MASSCAN_RATE_TARGET")
CHECKER_WORKERS = get_int("CHECKER_WORKERS")
CHECKER_PORT_CONCURRENCY = get_int("CHECKER_PORT_CONCURRENCY")
MONITOR_SERVER_WORKERS = get_int("MONITOR_SERVER_WORKERS")
MONITOR_PLAYER_WORKERS = get_int("MONITOR_PLAYER_WORKERS")
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

API_MAX_ATTEMPTS = get_int("API_MAX_ATTEMPTS")
API_BASE_DELAY_SECONDS = get_int("API_BASE_DELAY_SECONDS")
API_MAX_DELAY_SECONDS = get_int("API_MAX_DELAY_SECONDS")
WORKER_RESTART_ON_FAILURE_DELAY = get_int("WORKER_RESTART_ON_FAILURE_DELAY")
MOJANG_BULK_URL = "https://api.mojang.com/profiles/minecraft"
SESSION_URL = "https://sessionserver.mojang.com/session/minecraft/profile"
MOJANG_SEMAPHORE = 400 // 10  # max 400 requests per 10 seconds
IPINFO_SEMAPHORE = 8

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
