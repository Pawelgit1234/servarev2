import { Buffer } from "node:buffer";
import { compress } from "@mongodb-js/zstd";
import type { SubChunk } from "./bot.js";

export type L4S_POTENTIAL = "not_affected" | "potentially_vulnerable" | "fixed";

export function determineL4sPotential(version: string): L4S_POTENTIAL {
  const [major, minor, patch = 0] = version.split(".").map(Number);

  if (major === 1 && minor! < 7) return "not_affected";
  if (major === 1 && minor! === 18 && patch === 0)
    return "potentially_vulnerable";
  if (major === 1 && minor! < 18) return "potentially_vulnerable";

  return "fixed";
}

export function collectStrings(value: unknown): string[] {
  if (typeof value === "string") return [value];

  if (Array.isArray(value)) return value.flatMap(collectStrings);

  if (value !== null && typeof value === "object")
    return Object.values(value).flatMap(collectStrings);

  return [];
}

export function getSignText(value: unknown): string {
  const strings: string[] = collectStrings(value);

  return strings
    .filter((string: string) => string !== '""' && string.includes('"'))
    .flatMap((string: string): string[] => {
      try {
        const parsed: unknown = JSON.parse(string);

        if (
          parsed !== null &&
          typeof parsed === "object" &&
          "text" in parsed &&
          typeof parsed.text === "string"
        ) {
          return [parsed.text];
        }

        return [String(parsed)];
      } catch {
        return [];
      }
    })
    .join(" ")
    .trim();
}

export function returnUnique(values: string[]): string[] {
  return [...new Set(values)];
}

export function joinOrNull(values: string[]): string | null {
  return values.length > 0 ? values.join("\n") : null;
}

export async function serializeWorld(subChunks: SubChunk[]): Promise<Buffer> {
  const parts: Buffer[] = [];

  // Magic + version
  const header = Buffer.allocUnsafe(5);

  header.write("SVW2", 0, "ascii");
  header.writeUInt8(1, 4);

  parts.push(header);

  // Number of subchunks
  const count = Buffer.allocUnsafe(4);
  count.writeUInt32BE(subChunks.length, 0);

  parts.push(count);

  for (const subChunk of subChunks) {
    const data = Buffer.from(
      subChunk.data.buffer,
      subChunk.data.byteOffset,
      subChunk.data.byteLength,
    );

    // x, y, z, bitsPerValue, paletteLength, dataLength
    const metadata = Buffer.allocUnsafe(4 + 4 + 4 + 1 + 4 + 4);

    let offset = 0;

    metadata.writeInt32BE(subChunk.x, offset);
    offset += 4;

    metadata.writeInt32BE(subChunk.y, offset);
    offset += 4;

    metadata.writeInt32BE(subChunk.z, offset);
    offset += 4;

    metadata.writeUInt8(subChunk.bitsPerValue, offset);
    offset += 1;

    metadata.writeUInt32BE(subChunk.palette.length, offset);
    offset += 4;

    metadata.writeUInt32BE(data.length, offset);

    const palette = Buffer.allocUnsafe(subChunk.palette.length * 4);

    for (let i = 0; i < subChunk.palette.length; i++) {
      palette.writeUInt32BE(subChunk.palette[i]!, i * 4);
    }

    parts.push(metadata);
    parts.push(palette);
    parts.push(data);
  }

  const uncompressed = Buffer.concat(parts);

  // Zstd compression level 10
  return compress(uncompressed, 10);
}
