import subprocess

from common.settings import MASSCAN_RATE


def scan_java() -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            "stdbuf",
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
            line = proc.stdout.readline().strip()  # type: ignore

            if not line:
                break

            if "open" in line:
                print(line, flush=True)


if __name__ == "__main__":
    main()
