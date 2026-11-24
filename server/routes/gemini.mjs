import { generateText } from "../gemini-client.mjs";
import { mapGeminiError } from "../gemini-errors.mjs";
import { sendJson } from "../http-utils.mjs";
import { validateGenerateBody } from "./validate-prompt.mjs";

export { validateGenerateBody };

/**
 * @param {import("node:http").IncomingMessage} req
 * @param {import("node:http").ServerResponse} res
 * @param {string | null} corsOrigin
 * @param {string} rawBody
 */
export async function handleGeminiGenerate(req, res, corsOrigin, rawBody) {
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

    const validation = validateGenerateBody(parsed);
    if (!validation.ok) {
        sendJson(res, 400, {
            error: validation.message,
            code: validation.code,
        }, corsOrigin);
        return;
    }

    try {
        const text = await generateText(validation.prompt);
        sendJson(res, 200, { text }, corsOrigin);
    } catch (err) {
        const code = err && typeof err === "object" && "code" in err ? String(err.code) : "GEMINI_ERROR";

        if (code === "CONFIG_MISSING_API_KEY") {
            sendJson(res, 503, {
                error: "Gemini is not configured on the server.",
                code,
            }, corsOrigin);
            return;
        }

        console.error("[gemini] request failed:", err);
        const mapped = mapGeminiError(err);
        sendJson(res, mapped.httpStatus, {
            error: mapped.error,
            code: mapped.code,
        }, corsOrigin);
    }
}