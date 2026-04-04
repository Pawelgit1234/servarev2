import logging
import subprocess

from common.databases import rs
from common.logger import setup_logging
from common.settings import MASSCAN_RATE, REDIS_IP_QUEUE

setup_logging()
logger = logging.getLogger(__name__)


def scan_java() -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            "stdbuf",  # important
            "-oL",  # important
            "masscan",
            "0.0.0.0/0",
            "-p25565",
            "--rate",
            str(MASSCAN_RATE),
            "-oL",
            "-",
            "--excludefile",
            "./exclude.conf",
        ],
        stdout=subprocess.PIPE,
        text=True,
    )


def main() -> None:
    while True:
        proc = scan_java()

        while True:
            line = proc.stdout.readline()  # type: ignore

            if not line:
                logger.info("Out of ips")
                break

            line = line.strip()
            if "open" in line:
                rs.rpush(REDIS_IP_QUEUE, line)


if __name__ == "__main__":
    main()
