import { cp, mkdir, readdir, readFile, writeFile, rm } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

function normalizeApiBase(value) {
    if (typeof value !== "string") {
        return "";
    }
    return value.trim().replace(/\/$/, "");
}

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
            filter: (source) => {
                const base = source.split(/[\\/]/).pop();
                if (base.startsWith(".")) {
                    return false;
                }
                if (base === "unifit-api-config.js") {
                    return false;
                }
                return true;
            },
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

const apiBase = normalizeApiBase(process.env.UNIFIT_API_BASE || "");
const onVercelProduction = process.env.VERCEL === "1" && process.env.VERCEL_ENV === "production";
if (onVercelProduction && !apiBase) {
    console.error(
        "UNIFIT_API_BASE is missing. Add it in Vercel → Settings → Environment Variables "
        + "(Production) with your Render API URL, then redeploy.",
    );
    process.exit(1);
}

if (apiBase) {
    const searchHtmlPath = join(output, "search.html");
    let html = await readFile(searchHtmlPath, "utf8");
    const escaped = apiBase.replace(/"/g, "&quot;");
    const metaTag = `<meta name="unifit-api-base" content="${escaped}">`;
    const inlineTag = `<script id="unifit-api-base-inline">window.__UNIFIT_API_BASE__=${JSON.stringify(apiBase)};</script>`;
    if (html.includes('name="unifit-api-base"')) {
        html = html.replace(
            /<meta\s+name="unifit-api-base"\s+content="[^"]*"\s*\/?>/i,
            metaTag,
        );
    } else {
        html = html.replace(
            /<meta\s+name="viewport"[^>]*>/i,
            (match) => `${match}\n  ${metaTag}\n  ${inlineTag}`,
        );
    }
    if (!html.includes("unifit-api-base-inline")) {
        html = html.replace(
            /<meta\s+name="unifit-api-base"[^>]*>/i,
            (match) => `${match}\n  ${inlineTag}`,
        );
    }
    await writeFile(searchHtmlPath, html, "utf8");
}
