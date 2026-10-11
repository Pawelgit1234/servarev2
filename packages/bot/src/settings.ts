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
  S3_ENDPOINT: "http://minio:9000",
  S3_REGION_NAME: "us-east-1",
  S3_WORLD_PREFIX: "world",
  S3_BUCKET: "assets",

  BOT_WORKERS: Number(requiredEnv("BOT_WORKERS")),
  DB_RETRY_DELAY_SECONDS: Number(requiredEnv("DB_RETRY_DELAY_SECONDS")),
  BOT_IDLE_TIMEOUT: Number(requiredEnv("BOT_IDLE_TIMEOUT")),
  BOT_CONNECT_TIMEOUT: Number(requiredEnv("BOT_CONNECT_TIMEOUT")) * 1000,
  BOT_MAX_LIFETIME: Number(requiredEnv("BOT_MAX_LIFETIME")),
  BOT_NAME_PREFIX: requiredEnv("BOT_NAME_PREFIX"),
  BOT_NAME_LENGTH: 10,
  BOT_SPAWN_MESSAGE: requiredEnv("BOT_SPAWN_MESSAGE"),
  WORKER_RESTART_ON_FAILURE_DELAY: Number(requiredEnv("WORKER_RESTART_ON_FAILURE_DELAY"))
};
