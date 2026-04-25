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

REDIS_HOST = "redis"
REDIS_PORT = 6379

MULTIPORT_IPS_FILEPATH = "./multiport_ips.txt"

REDIS_IP_QUEUE = "ips"

MASSCAN_RATE = get_int("MASSCAN_RATE")
CHECK_CONCURRENCY = get_int("CHECK_CONCURRENCY")
SERVER_CHECK_TIMEOUT = get_int("SERVER_CHECK_TIMEOUT")

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
PLAYER_SEMAPHORE_COUNT = 400 // 10  # max 400 requests per 10 seconds
