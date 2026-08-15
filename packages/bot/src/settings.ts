import process from "node:process";

function requiredEnv(name: string): string {
    const value = process.env[name];

    if (value === undefined) {
        throw new Error(`Required environment variable ${name} is not set`);
    }

    return value;
}

export const settings = {
    DB_USERNAME: requiredEnv("DB_USERNAME"),
    DB_PASSWORD: requiredEnv("DB_PASSWORD"),
    DB_NAME: requiredEnv("DB_NAME"),
    DB_HOST: requiredEnv("DB_HOST"),
    DB_PORT: Number(requiredEnv("DB_PORT")),
    DB_POOL_SIZE: Number(requiredEnv("DB_POOL_SIZE")),
    DB_MAX_OVERFLOW: Number(requiredEnv("DB_MAX_OVERFLOW")),
    DB_POOL_TIMEOUT: Number(requiredEnv("DB_POOL_TIMEOUT")),
    S3_PUBLIC_ENDPOINT: requiredEnv("S3_PUBLIC_ENDPOINT"),
    S3_ROOT_USER: requiredEnv("S3_ROOT_USER"),
    S3_ROOT_PASSWORD: requiredEnv("S3_ROOT_PASSWORD"),
    BOT_WORKERS: Number(requiredEnv("BOT_WORKERS")),
    DB_RETRY_DELAY_SECONDS: Number(requiredEnv("DB_RETRY_DELAY_SECONDS")),
};