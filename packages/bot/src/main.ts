import { logger } from "./logger.js";
import { settings } from "./settings.js";
import { getNextServer } from "./services.js";
import { sleep } from "./utils.js";

async function worker(): Promise<void> {
    while (true) {
        const result = await getNextServer()
        if (result === undefined) {
            logger.warn("Database is empty: no servers")
            await sleep(settings.DB_RETRY_DELAY_SECONDS)
            continue
        }
        const { server, ip } = result;
        

        // TODO: обновление даты lastBotCheckAt
    }
}

async function main(): Promise<void> {
    logger.info("Starts running");

    // TODO: worker protection like in monitor and checker + starting worker log etc
    await Promise.all(
        Array.from(
            { length: settings.BOT_WORKERS },
            () => worker(),
        )
    )
}

main();