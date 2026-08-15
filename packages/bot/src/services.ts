import { asc, eq } from "drizzle-orm";
import { db } from "./db/database.js";
import { ips, servers } from "./db/schema.js";


// TODO: get_next_server()
// server с самым старым last_bot_check_at -> IpModel => получается ip:port
// нужна вся модел сервера, чтобы можно было удобно просто поверх навесить
// нужные данные

// TODO: проанализировать, как я делал это в monitor и checker

export async function getNextServer() {
    return db.transaction(async (tx) => {
        const [result] = await tx
            .select({
                server: servers,
                ip: ips,
            })
            .from(servers)
            .innerJoin(ips, eq(servers.ipId, ips.id))
            .orderBy(asc(servers.lastBotCheckAt))
            .limit(1)
            .for("update", { skipLocked: true });

        return result;
    });
}