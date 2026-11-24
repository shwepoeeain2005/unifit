import http from "node:http";
import url from "node:url";
import "./load-env.mjs";
import { isOpenRouterConfigured } from "./openrouter-env.mjs";
import {
    ASSISTANT_CHAT_PATH,
    DEFAULT_BIND,
    DEFAULT_PORT,
    GEMINI_GENERATE_PATH,
    MAX_BODY_BYTES,
} from "./config.mjs";
import {
    readBody,
    resolveCorsOrigin,
    sendJson,
    setCorsHeaders,
} from "./http-utils.mjs";
import { handleAssistantChat } from "./routes/assistant.mjs";
import { handleGeminiGenerate } from "./routes/gemini.mjs";

function normalizeEnvFlag(value) {
    if (value === undefined || value === null) {
        return false;
    }
    const normalized = String(value).trim().toLowerCase();
    return normalized === "1" || normalized === "true" || normalized === "yes";
}

const port = Number(process.env.PORT) || DEFAULT_PORT;
/** Render and similar hosts set PORT; bind on all interfaces unless BIND is set explicitly. */
const bind = process.env.BIND || (process.env.PORT ? "0.0.0.0" : DEFAULT_BIND);

const geminiRollbackEnabled = normalizeEnvFlag(process.env.ENABLE_GEMINI_ROLLBACK_ROUTE);

/** @type {Record<string, typeof handleGeminiGenerate>} */
const generateHandlers = {};

if (geminiRollbackEnabled) {
    generateHandlers[GEMINI_GENERATE_PATH] = handleGeminiGenerate;
}

const generatePaths = new Set(Object.keys(generateHandlers));
const apiPostPaths = new Set([...generatePaths, ASSISTANT_CHAT_PATH]);

/**
 * @param {import("node:http").IncomingMessage} req
 * @returns {string}
 */
function requestPathname(req) {
    return url.parse(req.url || "/", false).pathname || "/";
}

const server = http.createServer(async (req, res) => {
    const pathname = requestPathname(req);
    const corsOrigin = resolveCorsOrigin(req);

    if (req.method === "OPTIONS" && apiPostPaths.has(pathname)) {
        setCorsHeaders(res, corsOrigin);
        res.statusCode = 204;
        res.end();
        return;
    }

    const handler = generateHandlers[pathname];
    const isAssistantChat = pathname === ASSISTANT_CHAT_PATH;
    if (!handler && !isAssistantChat) {
        sendJson(res, 404, { error: "Not found.", code: "NOT_FOUND" }, corsOrigin);
        return;
    }

    if (req.method !== "POST") {
        sendJson(res, 405, {
            error: "Method not allowed. Use POST.",
            code: "METHOD_NOT_ALLOWED",
        }, corsOrigin);
        return;
    }

    const contentType = (req.headers["content-type"] || "").split(";")[0].trim().toLowerCase();
    if (contentType && contentType !== "application/json") {
        sendJson(res, 415, {
            error: "Content-Type must be application/json.",
            code: "UNSUPPORTED_MEDIA_TYPE",
        }, corsOrigin);
        return;
    }

    let rawBody;
    try {
        rawBody = await readBody(req, MAX_BODY_BYTES);
    } catch (err) {
        if (err && typeof err === "object" && err.code === "PAYLOAD_TOO_LARGE") {
            sendJson(res, 413, {
                error: `Request body must not exceed ${MAX_BODY_BYTES} bytes.`,
                code: "PAYLOAD_TOO_LARGE",
            }, corsOrigin);
            return;
        }
        console.error("[server] failed to read body:", err);
        sendJson(res, 400, {
            error: "Could not read request body.",
            code: "BODY_READ_ERROR",
        }, corsOrigin);
        return;
    }

    if (isAssistantChat) {
        await handleAssistantChat(req, res, corsOrigin, rawBody);
        return;
    }

    await handler(req, res, corsOrigin, rawBody);
});

server.listen(port, bind, () => {
    console.log(`UniFit API listening at http://${bind}:${port}`);
    console.log(`  POST ${ASSISTANT_CHAT_PATH}`);
    if (geminiRollbackEnabled) {
        console.log(`  POST ${GEMINI_GENERATE_PATH} (Gemini rollback)`);
    }
    console.log(`  OpenRouter env: ${isOpenRouterConfigured() ? "ready" : "not configured"}`);
});