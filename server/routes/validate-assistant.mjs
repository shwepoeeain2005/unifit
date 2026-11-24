import { MAX_PROMPT_CHARS } from "../config.mjs";

/**
 * @param {unknown} body
 * @returns {{
 *   ok: true,
 *   message: string,
 *   searchContext: Record<string, unknown> | null
 * } | { ok: false, code: string, message: string }
 * }
 */
export function validateAssistantChatBody(body) {
    if (body === null || typeof body !== "object" || Array.isArray(body)) {
        return {
            ok: false,
            code: "INVALID_JSON_BODY",
            message: "Request body must be a JSON object with a \"message\" field.",
        };
    }

    const record = /** @type {Record<string, unknown>} */ (body);
    const rawMessage = record.message;
    if (typeof rawMessage !== "string") {
        return {
            ok: false,
            code: "INVALID_MESSAGE",
            message: "The \"message\" field must be a non-empty string.",
        };
    }

    const trimmed = rawMessage.trim();
    if (!trimmed) {
        return {
            ok: false,
            code: "EMPTY_MESSAGE",
            message: "The \"message\" field cannot be empty.",
        };
    }

    if (trimmed.length > MAX_PROMPT_CHARS) {
        return {
            ok: false,
            code: "MESSAGE_TOO_LONG",
            message: `The "message" field must be at most ${MAX_PROMPT_CHARS} characters.`,
        };
    }

    let searchContext = null;
    if ("searchContext" in record && record.searchContext !== undefined && record.searchContext !== null) {
        if (typeof record.searchContext !== "object" || Array.isArray(record.searchContext)) {
            return {
                ok: false,
                code: "INVALID_SEARCH_CONTEXT",
                message: "The \"searchContext\" field must be an object when provided.",
            };
        }
        searchContext = /** @type {Record<string, unknown>} */ (record.searchContext);
    }

    return { ok: true, message: trimmed, searchContext };
}