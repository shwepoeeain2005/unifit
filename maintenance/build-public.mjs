import { cp, mkdir, readdir, rm } from "node:fs/promises";
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
