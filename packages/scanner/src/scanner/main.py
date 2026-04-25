import logging
import subprocess
from pathlib import Path

from common.databases import rs
from common.logger import setup_logging
from common.settings import (
    MASSCAN_RATE,
    MULTIPORT_IPS_FILEPATH,
    REDIS_IP_QUEUE,
)

setup_logging()
logger = logging.getLogger(__name__)

IPS_FILE = Path(MULTIPORT_IPS_FILEPATH)


def run_masscan(args: list[str]) -> subprocess.Popen[str]:
    """Runs masscan"""

    return subprocess.Popen(
        [
            "stdbuf",
            "-oL",
            "masscan",
            *args,
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


def process_output(proc: subprocess.Popen[str]) -> None:
    """Sends open ports to checker"""

    while True:
        line = proc.stdout.readline()  # type: ignore

        if not line:
            break

        line = line.strip()
        if "open" in line:
            rs.rpush(REDIS_IP_QUEUE, line)


def scan_full_internet() -> None:
    """Scans the whole internet"""

    logger.info("Full internet scan")

    # TCP (Java Servers)
    process_output(
        run_masscan(
            [
                "0.0.0.0/0",
                "-p25565",
            ]
        )
    )

    # UDP (Bedrock Servers)
    process_output(
        run_masscan(
            [
                "0.0.0.0/0",
                "-pU:19132",
            ]
        )
    )


def scan_multiport_ips() -> None:
    """Scans hosts like Playit.gg"""

    if not IPS_FILE.exists():
        logger.warning("multiport_ips.txt not found, skipping")
        return

    logger.info("Multiport ips scan")

    # TCP (Java Servers)
    process_output(
        run_masscan(
            [
                "-iL",
                str(IPS_FILE),
                "-p1-65535",
            ]
        )
    )

    # UDP (Bedrock Servers)
    process_output(
        run_masscan(
            [
                "-iL",
                str(IPS_FILE),
                "-pU:1-65535",
            ]
        )
    )


def main() -> None:
    while True:
        logger.info("Next cycle")
        scan_full_internet()
        scan_multiport_ips()


if __name__ == "__main__":
    main()
