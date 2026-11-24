/**
 * Netlify build: publish static site to dist/ without Node backend or tooling secrets.
 */
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const distRoot = path.join(repoRoot, "dist");

const EXCLUDE_TOP_LEVEL = new Set([
    "dist",
    "node_modules",
    "server",
    ".git",
    ".github",
    "maintenance",
    ".env",
    ".env.local",
    ".env.example",
    "README.md",
    ".gitignore",
    "package.json",
    "package-lock.json",
    "netlify.toml",
    "__pycache__",
]);

const EXCLUDE_MAINTENANCE_FILES = /\.(sqlite|sqlite-journal|sqlite-shm|sqlite-wal)$/i;

function shouldSkip(relFromRepo) {
    const parts = relFromRepo.split(path.sep).filter(Boolean);
    if (parts.length > 0 && EXCLUDE_TOP_LEVEL.has(parts[0])) {
        return true;
    }
    if (parts[0] === "maintenance" && parts.length > 1 && EXCLUDE_MAINTENANCE_FILES.test(parts[parts.length - 1])) {
        return true;
    }
    return false;
}

function copyDir(src, dest, rel = "") {
    fs.mkdirSync(dest, { recursive: true });
    for (const name of fs.readdirSync(src, { withFileTypes: true })) {
        if (name.name === "dist") {
            continue;
        }
        const relPath = rel ? `${rel}${path.sep}${name.name}` : name.name;
        if (shouldSkip(relPath)) {
            continue;
        }
        const from = path.join(src, name.name);
        const to = path.join(dest, name.name);
        if (name.isDirectory()) {
            copyDir(from, to, relPath);
        } else if (name.isFile()) {
            fs.copyFileSync(from, to);
        }
    }
}

if (fs.existsSync(distRoot)) {
    fs.rmSync(distRoot, { recursive: true, force: true });
}

copyDir(repoRoot, distRoot);

const configScript = path.join(repoRoot, "maintenance", "write-unifit-api-config.mjs");
const result = spawnSync(
    process.execPath,
    [configScript],
    {
        env: {
            ...process.env,
            UNIFIT_API_CONFIG_OUT: path.join(distRoot, "assets", "js", "unifit-api-config.js"),
        },
        stdio: "inherit",
    },
);

if (result.status !== 0) {
    process.exit(result.status ?? 1);
}

console.log("Netlify dist ready:", distRoot);