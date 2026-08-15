import { drizzle } from "drizzle-orm/node-postgres";
import pg from "pg";

import { settings } from "../settings.js";

const { Pool } = pg;

const pool = new Pool({
    host: settings.DB_HOST,
    port: settings.DB_PORT,
    user: settings.DB_USERNAME,
    password: settings.DB_PASSWORD,
    database: settings.DB_NAME,
    max: settings.DB_POOL_SIZE,
    connectionTimeoutMillis: settings.DB_POOL_TIMEOUT * 1000,
});

export const db = drizzle(pool);