import { asc, eq, sql, inArray } from "drizzle-orm";
import { db } from "./db/database.js";
import { ips, servers, resourcePacks, serverBotSnapshotResourcePackAssociations } from "./db/schema.js";
import type { BotData } from "./bots/bot.js";
import { serverBotSnapshots } from "./db/schema.js";

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

    if (result === undefined) {
      return undefined;
    }

    // update lastBotCheckAt
    await tx
      .update(servers)
      .set({ lastBotCheckAt: sql`now()` })
      .where(eq(servers.id, result.server.id));

    return result;
  });
}

export async function saveBotData(
  serverId: number,
  worldHash: string | null,
  botData: BotData,
) {
  return db.transaction(async (tx) => {
    const [snapshot] = await tx
      .insert(serverBotSnapshots)
      .values({
        serverId,
        hash: worldHash,

        isWhitelisted: botData.isWhitelisted,
        isHardcore: botData.isHardcore,

        connection: botData.connectionEvents,
        signs: botData.signs,
        chat: botData.chat,
        scoreboards: botData.scoreboards,

        gameMode: botData.gameMode,
        difficulty: botData.difficulty,
      })
      .returning();

    if (snapshot === undefined) {
      throw new Error("Failed to create bot snapshot")
    }

    if (botData.resourcePacks.length === 0) {
      return snapshot;
    }

    // Create existing resourcePacks
    await tx
      .insert(resourcePacks)
      .values(
        botData.resourcePacks.map((pack) => ({
          url: pack.url,
          hash: pack.hash ?? null,
        })),
      )
      .onConflictDoNothing({
        target: resourcePacks.url,
      });

    // Get packs
    const packs = await tx
      .select({
        id: resourcePacks.id,
        url: resourcePacks.url,
      })
      .from(resourcePacks)
      .where(
        inArray(
          resourcePacks.url,
          botData.resourcePacks.map((pack) => pack.url),
        ),
      );

    // Associations
    await tx
      .insert(serverBotSnapshotResourcePackAssociations)
      .values(
        packs.map((pack) => ({
          botSnapshotId: snapshot.id,
          resourcePackId: pack.id,
        })),
      )
      .onConflictDoNothing();

    return snapshot;
  });
}
