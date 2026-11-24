/**
 * Write assets/js/unifit-api-config.js from UNIFIT_API_BASE (Vercel/Netlify build env).
 * No secrets — public Render API origin only.
 *
 * Usage:
 *   node maintenance/write-unifit-api-config.mjs
 *   UNIFIT_API_CONFIG_OUT=dist/assets/js/unifit-api-config.mjs node maintenance/...
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function normalizeApiBase(value) {
    if (typeof value !== "string") {
        return "";
    }
    return value.trim().replace(/\/$/, "");
}

const apiBase = normalizeApiBase(process.env.UNIFIT_API_BASE || "");
const onVercel = process.env.VERCEL === "1";
if (onVercel && !apiBase) {
    console.error(
        "UNIFIT_API_BASE is missing or empty. In Vercel → Project → Settings → Environment Variables, "
        + "set UNIFIT_API_BASE for Production and enable it for Builds, then redeploy.",
    );
    process.exit(1);
}

const outRel = process.env.UNIFIT_API_CONFIG_OUT || "assets/js/unifit-api-config.js";
const outPath = path.isAbsolute(outRel) ? outRel : path.join(repoRoot, outRel);

const contents = `/* Generated at build time — set UNIFIT_API_BASE in Vercel/Netlify build environment. */
(function (root) {
    root.__UNIFIT_API_BASE__ = ${JSON.stringify(apiBase)};
})(typeof globalThis !== "undefined" ? globalThis : typeof window !== "undefined" ? window : this);
`;

fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, contents, "utf8");
console.log(`Wrote ${path.relative(repoRoot, outPath)} (UNIFIT_API_BASE=${apiBase ? "set" : "empty"})`);