import logging
import subprocess
from collections import defaultdict

from common.databases import rs
from common.logger import setup_logging
from common.settings import (
    MASSCAN_RATE_TARGET,
    PORTER_BATCH_SIZE,
    REDIS_IP_QUEUE,
    REDIS_PORTER_QUEUE,
)

setup_logging()
logger = logging.getLogger(__name__)


def run_masscan(ips: list[str]) -> subprocess.Popen[str]:
    """Runs masscan for multiple IPs"""

    return subprocess.Popen(
        [
            "stdbuf",
            "-oL",
            "masscan",
            *ips,
            "-p1-65535",  # TODO: ,U:1-65535
            "--rate",
            str(MASSCAN_RATE_TARGET),
            "-oL",
            "-",
        ],
        stdout=subprocess.PIPE,
        text=True,
    )


def scan_ips(ips: list[str]) -> dict[str, str]:
    """
    Scans all IP ports.

    Returns:
        {
            "1.1.1.1": "tcp:22,80,443,25565|udp:19132",
            ...
        }
    """

    proc = run_masscan(ips)

    tcp_ports: dict[str, list[str]] = defaultdict(list)
    udp_ports: dict[str, list[str]] = defaultdict(list)

    while True:
        line = proc.stdout.readline()  # type: ignore

        if not line:
            break

        line = line.strip()

        # format:
        # open tcp 25565 1.1.1.1 ...
        if "open" not in line:
            continue

        parts = line.split()

        protocol = parts[1]
        port = parts[2]
        ip = parts[3]

        if protocol == "tcp":
            tcp_ports[ip].append(port)
        else:
            udp_ports[ip].append(port)

    proc.wait()

    results = {}

    for ip in ips:
        tcp = ",".join(tcp_ports[ip])
        udp = ",".join(udp_ports[ip])

        results[ip] = f"tcp:{tcp}|udp:{udp}"

    return results


def get_ip_batch(size: int) -> list[str]:
    """Waits until enough IPs are collected"""

    ips: list[str] = []

    while len(ips) < size:
        ip = rs.blpop(REDIS_PORTER_QUEUE)[1]
        ips.append(ip)

    return ips


def main() -> None:
    logger.info("Starts running")

    while True:
        ips = get_ip_batch(PORTER_BATCH_SIZE)  # type: ignore

        logger.info(f"{ips} scan start")
        results = scan_ips(ips)

        pipe = rs.pipeline()

        for ip, ports in results.items():
            pipe.rpush(REDIS_IP_QUEUE, f"{ports} {ip}")

        pipe.execute()


if __name__ == "__main__":
    main()
