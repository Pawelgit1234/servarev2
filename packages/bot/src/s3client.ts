import {
  S3Client as AwsS3Client,
  HeadBucketCommand,
  HeadObjectCommand,
  PutObjectCommand,
} from "@aws-sdk/client-s3";
import { logger } from "./logger.js";
import { createHash } from "node:crypto";
import { settings } from "./settings.js";

class S3Client {
  private readonly client: AwsS3Client;
  private readonly bucketName: string;

  private bucketReady = false;

  constructor(
    accessKey: string,
    secretKey: string,
    endpointUrl: string,
    bucketName: string,
    regionName: string,
  ) {
    this.client = new AwsS3Client({
      credentials: {
        accessKeyId: accessKey,
        secretAccessKey: secretKey,
      },
      endpoint: endpointUrl,
      region: regionName,
      forcePathStyle: true,
    });

    this.bucketName = bucketName;
  }

  private async checkIfBucketExists(): Promise<void> {
    if (this.bucketReady) return;

    try {
      await this.client.send(
        new HeadBucketCommand({
          Bucket: this.bucketName,
        }),
      );

      this.bucketReady = true;
    } catch (error) {
      logger.warn(`S3 bucket "${this.bucketName}" does not exist`);
    }
  }

  private async fileExists(key: string): Promise<boolean> {
    try {
      await this.client.send(
        new HeadObjectCommand({
          Bucket: this.bucketName,
          Key: key,
        }),
      );

      return true;
    } catch {
      return false;
    }
  }

  public async uploadBytes(
    data: Buffer,
    objectName: string | undefined,
    prefix: string,
    contentType?: string,
    deduplicate = false,
  ): Promise<string | null> {
    await this.checkIfBucketExists();
    if (!this.bucketReady) return null;

    if (objectName === undefined) {
      objectName = createHash("md5").update(data).digest("hex");
    }

    const key = `${prefix}/${objectName}`;

    if (deduplicate) {
      if (await this.fileExists(key)) {
        return objectName;
      }
    }

    await this.client.send(
      new PutObjectCommand({
        Bucket: this.bucketName,
        Key: key,
        Body: data,
        ...(contentType !== undefined ? { ContentType: contentType } : {}),
      }),
    );

    return objectName;
  }
}

export const s3 = new S3Client(
  settings.S3_ROOT_USER,
  settings.S3_ROOT_PASSWORD,
  settings.S3_ENDPOINT,
  settings.S3_BUCKET,
  settings.S3_REGION_NAME,
);
