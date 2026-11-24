import { DEFAULT_CORS_ORIGINS } from "./config.mjs";

function parseCorsOrigins() {
    const raw = process.env.CORS_ORIGINS;
    if (!raw || !raw.trim()) {
        return DEFAULT_CORS_ORIGINS;
    }
    return raw.split(",").map((item) => item.trim()).filter(Boolean);
}

const allowedOrigins = parseCorsOrigins();

/**
 * @param {import("node:http").IncomingMessage} req
 * @returns {string | null}
 */
export function resolveCorsOrigin(req) {
    const origin = req.headers.origin;
    if (!origin) {
        return null;
    }
    if (allowedOrigins.includes(origin)) {
        return origin;
    }
    return null;
}

/**
 * @param {import("node:http").ServerResponse} res
 * @param {string | null} origin
 */
export function setCorsHeaders(res, origin) {
    if (!origin) {
        return;
    }
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Vary", "Origin");
    res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
}

/**
 * @param {import("node:http").ServerResponse} res
 * @param {number} status
 * @param {Record<string, unknown>} body
 * @param {string | null} [corsOrigin]
 */
export function sendJson(res, status, body, corsOrigin = null) {
    setCorsHeaders(res, corsOrigin);
    res.statusCode = status;
    res.setHeader("Content-Type", "application/json; charset=utf-8");
    res.end(JSON.stringify(body));
}

/**
 * @param {import("node:http").IncomingMessage} req
 * @param {number} maxBytes
 * @returns {Promise<string>}
 */
export function readBody(req, maxBytes) {
    return new Promise((resolve, reject) => {
        const chunks = [];
        let size = 0;

        req.on("data", (chunk) => {
            size += chunk.length;
            if (size > maxBytes) {
                req.destroy();
                reject(Object.assign(new Error("Payload too large"), { code: "PAYLOAD_TOO_LARGE" }));
                return;
            }
            chunks.push(chunk);
        });

        req.on("end", () => {
            resolve(Buffer.concat(chunks).toString("utf8"));
        });

        req.on("error", (err) => {
            reject(err);
        });
    });
}