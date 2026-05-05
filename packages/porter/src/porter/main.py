import logging
import subprocess

from common.databases import rs
from common.logger import setup_logging
from common.settings import (
    MASSCAN_RATE_TARGET,
    REDIS_IP_QUEUE,
    REDIS_PORTER_QUEUE,
)

setup_logging()
logger = logging.getLogger(__name__)


def run_masscan(ip: str, ports: str) -> subprocess.Popen[str]:
    """Runs masscan"""

    return subprocess.Popen(
        [
            "stdbuf",
            "-oL",
            "masscan",
            ip,
            ports,
            "--rate",
            str(MASSCAN_RATE_TARGET),
            "-oL",
            "-",
        ],
        stdout=subprocess.PIPE,
        text=True,
    )


def scan_ip(ip: str) -> str:
    """Scans all ip ports (tcp + udp in one run)"""

    proc = run_masscan(ip, "-p1-65535")  # TODO: ,U:1-65535

    ports = "tcp:"
    udp_ports = []

    while True:
        line = proc.stdout.readline()  # type: ignore
        if not line:
            break

        line = line.strip()

        # format: open tcp 25565 x.x.x.x ...
        if "open" in line:
            parts = line.split()
            protocol = parts[1]
            port = parts[2]

            if protocol == "tcp":
                ports += port + ","
            else:
                udp_ports.append(port)

    proc.wait()

    ports += "|" + "udp:" + ",".join(udp_ports)

    # e.g. tcp:21,22,80,|udp:19132,8888
    return ports


def main() -> None:
    logger.info("Starts running")
    while True:
        ip = (rs.blpop(REDIS_PORTER_QUEUE))[1]

        logger.info(f"{ip} scan start")
        ports = scan_ip(ip)

        rs.rpush(REDIS_IP_QUEUE, f"{REDIS_PORTER_QUEUE} {ports} {ip}")


if __name__ == "__main__":
    main()
