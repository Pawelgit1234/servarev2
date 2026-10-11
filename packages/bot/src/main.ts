import { logger } from "./logger.js";
import { settings } from "./settings.js";
import { getNextServer, saveBotData } from "./services.js";
import { randomWord, sleep } from "./utils.js";
import { Bot } from "./bots/bot.js";
import { s3 } from "./s3client.js";

// TODO: 1. todo.txt
//       2. перенести ldap сервер

async function runWorker(
  workerId: number,
  worker: () => Promise<void>,
): Promise<void> {
  while (true) {
    try {
      logger.info(`Starting bot-worker-${workerId}`);

      await worker();
    } catch (error) {
      logger.error(
        `Bot-worker-${workerId} crashed: ${
          error instanceof Error
            ? (error.stack ?? error.message)
            : String(error)
        }`,
      );

      await sleep(settings.WORKER_RESTART_ON_FAILURE_DELAY);
    }
  }
}

async function worker(): Promise<void> {
  while (true) {
    const result = await getNextServer();
    if (result === undefined) {
      logger.warn("Database is empty: no servers");
      await sleep(settings.DB_RETRY_DELAY_SECONDS);
      continue;
    }

    const { server, ip } = result;
    const username = `${settings.BOT_NAME_PREFIX}${randomWord(
      settings.BOT_NAME_LENGTH - settings.BOT_NAME_PREFIX.length,
    )}`;

    // TODO: write into redis about l4s + expire

    logger.info(`Join attempt [${username}]: ${ip.ip}:${server.port}`)

    const bot = new Bot(
      {
        host: ip.ip,
        port: server.port,
        username: username,
        closeTimeout: settings.BOT_CONNECT_TIMEOUT,
      },
      async (botData) => {
        // World upload
        const worldHash =
          botData.compressedWorld !== null
            ? await s3.uploadBytes(
                botData.compressedWorld,
                undefined,
                settings.S3_WORLD_PREFIX,
                undefined,
                true,
              )
            : null;

        await saveBotData(server.id, worldHash, botData);

        logger.info(`Snapshot of ${ip.ip}:${server.port} was saved`);
      },
    );
    await bot.wait();
  }
}

async function main(): Promise<void> {
  logger.info("Starts running");

  await Promise.all(
    Array.from(
      { length: settings.BOT_WORKERS },
      (_, workerId) => runWorker(workerId, worker),
    ),
  );
}

main()
