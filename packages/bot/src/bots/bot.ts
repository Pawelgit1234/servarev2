import mineflayer from "mineflayer";
import { difficultytype, gamemodetype } from "../db/schema.js";
import { settings } from "../settings.js";
import {
  getSignText,
  joinOrNull,
  returnUnique,
  serializeWorld,
} from "./utils.js";
import { logger } from "../logger.js";

type DifficultyType = (typeof difficultytype.enumValues)[number];
type GameModeType = (typeof gamemodetype.enumValues)[number];

export interface BotOptions {
  host: string;
  port: number;
  username: string;
  closeTimeout?: number;
}

interface ResourcePackData {
  url: string;
  hash: string | undefined;
}

export interface BotData {
  isWhitelisted: boolean | null;
  isHardcore: boolean | null;

  compressedWorld: Buffer | null;
  connectionEvents: string | null;
  signs: string | null;
  chat: string | null;
  scoreboards: string | null;

  gameMode: GameModeType | null;
  difficulty: DifficultyType | null;

  resourcePacks: ResourcePackData[];
}

type BotCallback = (botData: BotData) => Promise<void>;

export interface SubChunk {
  x: number;
  y: number;
  z: number;

  data: Uint32Array;
  palette: number[];
  bitsPerValue: number;
}

export class Bot {
  private readonly bot: mineflayer.Bot;

  private isWhitelisted: boolean | null = null;
  private isHardcore: boolean | null = null;

  private readonly subChunks: SubChunk[] = [];
  private readonly connectionEvents: string[] = [];
  private readonly signTexts: string[] = [];
  private readonly chatMessages: string[] = [];
  private readonly scoreboards: string[] = [];
  private readonly resourcePacks: ResourcePackData[] = [];

  private gameMode: GameModeType | null = null;
  private difficulty: DifficultyType | null = null;

  private idleTimeout?: NodeJS.Timeout | undefined;
  private maxTimeout?: NodeJS.Timeout | undefined;
  private connectTimeout: NodeJS.Timeout | undefined;

  private readonly callback: BotCallback;

  private finished = false;

  private readonly completion: Promise<void>;
  private resolveCompletion!: () => void;
  private rejectCompletion!: (error: unknown) => void;

  private readonly logString: string;

  constructor(options: BotOptions, callback: BotCallback) {
    this.callback = callback;
    this.logString = `[${options.username}] [${options.host}:${options.port}]:`;

    this.completion = new Promise<void>((resolve, reject) => {
      this.resolveCompletion = resolve;
      this.rejectCompletion = reject;
    });

    this.bot = mineflayer.createBot(options);

    this.registerEvents();

    this.connectTimeout = setTimeout(() => {
      const msg = `[error] Connection timeout after ${settings.BOT_CONNECT_TIMEOUT}ms`;
      logger.warn(`${this.logString} ${msg}`);

      this.quit();
    }, settings.BOT_CONNECT_TIMEOUT);
  }

  // Wait until the bot has completely finished its work,
  // including the callback (S3 upload, database save, etc.).
  public async wait(): Promise<void> {
    return this.completion;
  }

  private registerEvents(): void {
    this.bot.on("error", (error) => {
      const msg = `[error] ${error.name}: ${error.message}`;
      this.connectionEvents.push(msg);
      logger.info(`${this.logString} ${msg}`);
    });

    this.bot.on("kicked", (reason) => {
      const msg = `[kicked] ${JSON.stringify(reason)}`;
      this.connectionEvents.push(msg);

      if (JSON.stringify(reason).includes("multiplayer.disconnect.unverified_username")) {
        this.setWhitelist(true);
      }
      logger.info(`${this.logString} ${msg}`);
    });

    this.bot.once("end", async () => {
      await this.finish();
      logger.info(`${this.logString} end`);
    });

    this.bot.on("chunkColumnLoad", (point) => {
      this.resetIdleTimeout();

      try {
        const chunk = this.bot.world.getColumnAt(point);

        for (let i = -4; i < 20; i++) {
          const section = chunk.getSectionAtIndex(i);

          if (section === null || section === undefined) {
            continue;
          }

          this.subChunks.push({
            x: point.x / 16,
            y: i,
            z: point.y / 16,
            data: section.data.data.data,
            palette: section.data.palette,
            bitsPerValue: section.data.data.bitsPerValue,
          });
        }
      } catch (e) {
        logger.warn(`${this.logString} Chunk loading Error ${e}`);
      }
    });

    this.bot.on("scoreboardCreated", (scoreboard) => {
      this.resetIdleTimeout();

      const items = scoreboard.items.join(",");

      this.scoreboards.push(
        `[${scoreboard.name}] ${scoreboard.title}: ${items}`,
      );
    });

    this.bot.on("resourcePack", (url, hash) => {
      this.resetIdleTimeout();

      this.resourcePacks.push({ url, hash });
    });

    this.bot.on("messagestr", (message, _) => {
      this.resetIdleTimeout();

      const time = new Date().toISOString().split("T")[1]!.split(".")[0];

      this.chatMessages.push(`[${time}] ${message}`);
    });

    // Get text of signs, works for some versions.
    this.bot._client.on("packet", (data, meta) => {
      if (meta.name !== "map_chunk") {
        return;
      }

      this.resetIdleTimeout();

      data.blockEntities?.forEach((blockEntity: any) => {
        if (blockEntity.nbtData === undefined) {
          return;
        }

        const text = getSignText(blockEntity.nbtData);

        if (text !== "") {
          this.signTexts.push(text);
        }
      });
    });

    this.bot.once("spawn", () => {
      if (this.connectTimeout) {
        clearTimeout(this.connectTimeout);
        this.connectTimeout = undefined;
      }

      this.createTimeouts();

      logger.info(`${this.logString} spawn`);

      this.bot.chat(settings.BOT_SPAWN_MESSAGE);

      // Normal data.
      this.gameMode = this.bot.game.gameMode.toUpperCase() as GameModeType;
      this.difficulty =
        this.bot.game.difficulty.toUpperCase() as DifficultyType;
      this.isHardcore = this.bot.game.hardcore;
      this.setWhitelist(false);

      // Signs on older versions.
      const signIds = Object.values(this.bot.registry.blocksByName)
        .filter((block) => block.name.includes("sign"))
        .map((block) => block.id);

      const blocks = this.bot.findBlocks({
        matching: (block) => signIds.includes(block.type),
        maxDistance: 500,
        count: 10000,
      });

      blocks.forEach((position) => {
        const block = this.bot.blockAt(position);

        if (!block) {
          return;
        }

        const text = getSignText(block);

        if (text !== "") {
          this.signTexts.push(text);
        }
      });
    });
  }

  private createTimeouts(): void {
    this.maxTimeout = setTimeout(() => {
      this.quit();
    }, settings.BOT_MAX_LIFETIME);

    this.resetIdleTimeout();
  }

  private resetIdleTimeout(): void {
    if (this.idleTimeout) {
      clearTimeout(this.idleTimeout);
    }

    this.idleTimeout = setTimeout(() => {
      this.quit();
    }, settings.BOT_IDLE_TIMEOUT);
  }

  private clearTimeouts(): void {
    if (this.connectTimeout) {
      clearTimeout(this.connectTimeout);
      this.connectTimeout = undefined;
    }

    if (this.idleTimeout) {
      clearTimeout(this.idleTimeout);
      this.idleTimeout = undefined;
    }

    if (this.maxTimeout) {
      clearTimeout(this.maxTimeout);
      this.maxTimeout = undefined;
    }
  }

  private setWhitelist(whitelist: boolean): void {
    if (this.isWhitelisted !== null) {
      return;
    }

    this.isWhitelisted = whitelist;
  }

  public quit(): void {
    this.clearTimeouts();
    this.bot.end();
  }

  private async finish(): Promise<void> {
    if (this.finished) return;

    this.finished = true;
    this.clearTimeouts();

    logger.info(`${this.logString} finish`);

    try {
      const botData: BotData = {
        isWhitelisted: this.isWhitelisted,
        isHardcore: this.isHardcore,

        compressedWorld:
          this.subChunks.length === 0
            ? null
            : await serializeWorld(this.subChunks),

        gameMode: this.gameMode,
        difficulty: this.difficulty,

        resourcePacks: this.resourcePacks,
        connectionEvents: joinOrNull(returnUnique(this.connectionEvents)),
        signs: joinOrNull(returnUnique(this.signTexts)),
        chat: joinOrNull(returnUnique(this.chatMessages)),
        scoreboards: joinOrNull(returnUnique(this.scoreboards)),
      };

      logger.info(`${this.logString} callback`);
      await this.callback(botData);

      this.resolveCompletion();
    } catch (error) {
      logger.error(
        `${this.logString} Failed to finish bot: ${
          error instanceof Error
            ? (error.stack ?? error.message)
            : String(error)
        }`,
      );

      this.rejectCompletion(error);
    }
  }
}
