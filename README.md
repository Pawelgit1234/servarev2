# ServareV2

**A distributed Minecraft server discovery, scanning, monitoring, and data collection platform.**

ServareV2 is a monorepo containing a set of services designed to discover Minecraft servers, collect server information, monitor their availability, scan additional ports on discovered hosts, and gather world data through automated Minecraft bots.

The system combines network scanning, scheduled checks, persistent storage, and automated bot connections to maintain a continuously updated database of Minecraft servers and their associated information.

## Features

- **Server discovery** — discover Minecraft servers through automated network scanning.
- **Port scanning** — scan additional ports on discovered IP addresses to identify other potentially relevant services.
- **Continuous monitoring** — periodically recheck known servers and track their availability.
- **Automated bot connections** — connect Minecraft bots to servers to collect additional information.
- **World data collection** — use bots to retrieve and save Minecraft chunks.
- **Persistent storage** — store collected data and server information in PostgreSQL.
- **S3-compatible storage** — integrate with MinIO for object storage.
- **Configurable concurrency** — tune worker counts, connection concurrency, scan rates, and connection timeouts through environment variables.

## Architecture

ServareV2 is organized as a monorepo. Each application lives in its own package under `packages/`, while shared Python functionality is maintained in `packages/common/`.

### Services

| Service | Description |
|---|---|
| `scanner` | Discovers Ips that can possibly run Minecraft servers by searching for open ports 25565 and 19132. |
| `porter` | Performs additional port scanning using configurable scan rates and batch sizes. |
| `checker` | Checks server availability and collects server-related information. |
| `monitor` | Periodically rescans servers and players. |
| `bot` | Manages automated Minecraft bot connections for collecting server information and world data. |

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Pawelgit1234/servarev2.git
cd servareV2
```

### 2. Configure environment variables

Copy the example configuration:

```bash
mv example.env .env
```

Edit `.env` and configure the database credentials, scanning parameters, worker settings, storage credentials, and other required variables.

### 3. Build and start the services

```bash
docker compose up --build
```

## Security and Responsible Use

Network scanning can generate significant traffic and affect remote systems.

- Only scan networks and hosts you own or are explicitly authorized to test.
- Configure scanning rates and concurrency according to the target environment and available resources.
- Keep database credentials, API tokens, and object-storage secrets private.
- Review privileged container settings and host-network access before deployment.
- Restrict exposed database, Redis, MinIO, and administration interfaces to trusted users and networks.
- Monitor resource consumption when running large scans.

## Contributing

Contributions, bug reports, and improvements are welcome. Before submitting changes, ensure that the relevant services build correctly and that applicable tests pass.

