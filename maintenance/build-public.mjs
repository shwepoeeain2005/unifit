import { cp, mkdir, readdir, rm } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const root = fileURLToPath(new URL("../", import.meta.url));
const output = join(root, "dist");
await rm(output, { recursive: true, force: true });
await mkdir(output);

for (const entry of await readdir(root, { withFileTypes: true })) {
    const publish = entry.isDirectory()
        ? ["assets", "data", "universities"].includes(entry.name)
        : entry.isFile() && entry.name.endsWith(".html");
    if (publish) {
        await cp(join(root, entry.name), join(output, entry.name), {
            recursive: entry.isDirectory(),
            filter: source => !source.split(/[\\/]/).pop().startsWith("."),
        });
    }
}

const configOut = join(output, "assets", "js", "unifit-api-config.js");
const writeConfig = spawnSync(
    process.execPath,
    [join(root, "maintenance", "write-unifit-api-config.mjs")],
    {
        env: {
            ...process.env,
            UNIFIT_API_CONFIG_OUT: configOut,
        },
        stdio: "inherit",
    },
);

if (writeConfig.status !== 0) {
    process.exit(writeConfig.status ?? 1);
}
