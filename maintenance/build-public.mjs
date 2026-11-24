import { cp, mkdir, readdir, writeFile, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const root = fileURLToPath(new URL("../", import.meta.url));
const output = join(root, "dist");
const legacyConfigName = "unifit-api-config.js";

console.log("[build-public] start", {
    vercel: process.env.VERCEL === "1",
    vercelEnv: process.env.VERCEL_ENV || "",
    output: "dist",
});

await rm(output, { recursive: true, force: true });
await mkdir(output);

for (const entry of await readdir(root, { withFileTypes: true })) {
    const publish = entry.isDirectory()
        ? ["assets", "data", "universities"].includes(entry.name)
        : entry.isFile() && entry.name.endsWith(".html");
    if (publish) {
        await cp(join(root, entry.name), join(output, entry.name), {
            recursive: entry.isDirectory(),
            filter: (source) => {
                const base = source.split(/[\\/]/).pop();
                if (base.startsWith(".")) {
                    return false;
                }
                if (base === legacyConfigName) {
                    return false;
                }
                return true;
            },
        });
    }
}

const buildMarker = {
    builtAt: new Date().toISOString(),
    assistantApi: "same-origin:/api/assistant/chat",
    outputDirectory: "dist",
};
const buildMarkerJson = `${JSON.stringify(buildMarker)}\n`;
await writeFile(join(output, ".unifit-build.json"), buildMarkerJson, "utf8");
await writeFile(join(output, "unifit-build.json"), buildMarkerJson, "utf8");

console.log("[build-public] done", { output: "dist" });