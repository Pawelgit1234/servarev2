import { logger } from "./logger.js";
import { settings } from "./settings.js";
import { getNextServer } from "./services.js";
import { randomWord, sleep } from "./utils.js";
import { Bot } from "./bots/bot.js";

async function worker(): Promise<void> {
  while (true) {
    const result = await getNextServer();
    if (result === undefined) {
      logger.warn("Database is empty: no servers");
      await sleep(settings.DB_RETRY_DELAY_SECONDS);
      continue;
    }

    const { server, ip } = result;
    const username = `${settings.BOT_NAME_PREFIX}_${randomWord(settings.BOT_NAME_LENGTH - settings.BOT_NAME_PREFIX.length)}`;

    // TODO: write into redis about l4s

    new Bot(
      {
        host: ip.ip,
        port: server.port,
        username: username,
      },
      async (botData) => {
        // для будущего меня: просто посмотри, как я делал в handlers.py и
        // здесь похожим образом сделать
      },
    );

    // TODO: обновление даты lastBotCheckAt
  }
}

async function main(): Promise<void> {
  logger.info("Starts running");

  // TODO: worker protection like in monitor and checker + starting worker log etc
  await Promise.all(
    Array.from({ length: settings.BOT_WORKERS }, () => worker()),
  );
}

main();
