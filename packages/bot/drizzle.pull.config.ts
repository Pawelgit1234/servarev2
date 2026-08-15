import { defineConfig } from "drizzle-kit";
import { settings } from "./src/settings.js";

export default defineConfig({
    out: "./src/db",
    dialect: "postgresql",
    dbCredentials: {
        url: `postgresql://${settings.DB_USERNAME}:${settings.DB_PASSWORD}@${settings.DB_HOST}:${settings.DB_PORT}/${settings.DB_NAME}`
    }
})