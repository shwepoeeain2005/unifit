import dotenv from "dotenv";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

/**
 * Load .env from the git repo root first, then the parent workspace folder
 * (so keys work when .env sits in d:\unifit instead of d:\unifit\unifit).
 */
function loadEnvFiles() {
    const paths = [
        path.join(repoRoot, ".env"),
        path.join(repoRoot, "..", ".env"),
    ];
    for (const envPath of paths) {
        if (fs.existsSync(envPath)) {
            dotenv.config({ path: envPath, override: false });
        }
    }
}

loadEnvFiles();

export { repoRoot };