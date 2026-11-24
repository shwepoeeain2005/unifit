import { completeAssistantChat } from "../openrouter-client.mjs";
import { mapOpenRouterError } from "../openrouter-errors.mjs";
import { sendJson } from "../http-utils.mjs";
import { validateAssistantChatBody } from "./validate-assistant.mjs";

/**
 * @param {import("node:http").IncomingMessage} req
 * @param {import("node:http").ServerResponse} res
 * @param {string | null} corsOrigin
 * @param {string} rawBody
 */
export async function handleAssistantChat(req, res, corsOrigin, rawBody) {
    if (!rawBody.trim()) {
        sendJson(res, 400, {
            error: "Request body is required.",
            code: "EMPTY_BODY",
        }, corsOrigin);
        return;
    }

    let parsed;
    try {
        parsed = JSON.parse(rawBody);
    } catch {
        sendJson(res, 400, {
            error: "Request body must be valid JSON.",
            code: "INVALID_JSON",
        }, corsOrigin);
        return;
    }

    const validation = validateAssistantChatBody(parsed);
    if (!validation.ok) {
        sendJson(res, 400, {
            error: validation.message,
            code: validation.code,
        }, corsOrigin);
        return;
    }

    try {
        const reply = await completeAssistantChat(validation.message, validation.searchContext);
        sendJson(res, 200, { reply }, corsOrigin);
    } catch (err) {
        const code = err && typeof err === "object" && "code" in err ? String(err.code) : "ASSISTANT_ERROR";

        if (code === "CONFIG_MISSING_API_KEY" || code === "CONFIG_MISSING_MODEL") {
            sendJson(res, 503, {
                error: "The assistant is not configured on the server.",
                code: "AI_SERVICE_UNAVAILABLE",
            }, corsOrigin);
            return;
        }

        console.error("[assistant] request failed:", err);
        const mapped = mapOpenRouterError(err);
        sendJson(res, mapped.httpStatus, {
            error: mapped.error,
            code: mapped.code,
        }, corsOrigin);
    }
}