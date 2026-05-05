import logging
import subprocess
from pathlib import Path

from common.databases import rs
from common.logger import setup_logging
from common.settings import (
    EXCLUDE_IPS,
    MASSCAN_RATE,
    MULTIPORT_IPS_FILEPATH,
    REDIS_IP_QUEUE,
    SCANNER_ALL_IPS_SUFFIX,
    SCANNER_MULTIPORT_IP_SUFFIX,
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
            EXCLUDE_IPS,
        ],
        stdout=subprocess.PIPE,
        text=True,
    )


def process_output(proc: subprocess.Popen[str], suffix: str) -> None:
    """Sends open ports to checker"""

    while True:
        line = proc.stdout.readline()  # type: ignore

        if not line:
            break

        line = line.strip()

        if "open" in line:
            rs.rpush(REDIS_IP_QUEUE, f"{line} {suffix}")

    proc.wait()


def scan_full_internet() -> None:
    """Scans full internet (TCP + UDP in one pass)"""

    logger.info("Full internet scan")

    process_output(
        run_masscan(
            [
                "0.0.0.0/0",
                "-p25565",  # TODO: ,U:19132
            ]
        ),
        SCANNER_ALL_IPS_SUFFIX,
    )


def scan_multiport_ips() -> None:
    """Scans multiport IP list"""

    if not IPS_FILE.exists():
        logger.warning("multiport_ips.txt not found, skipping")
        return

    logger.info("Multiport IPs scan")

    process_output(
        run_masscan(
            [
                "-iL",
                str(IPS_FILE),
                "-p1-65535,U:1-65535",
            ]
        ),
        SCANNER_MULTIPORT_IP_SUFFIX,
    )


def main() -> None:
    logger.info("Starts running")
    while True:
        logger.info("Start of cycle")
        scan_full_internet()
        scan_multiport_ips()


if __name__ == "__main__":
    main()
