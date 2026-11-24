import { MAX_PROMPT_CHARS } from "../config.mjs";

/**
 * @param {unknown} body
 * @returns {{ ok: true, prompt: string } | { ok: false, code: string, message: string }}
 */
export function validateGenerateBody(body) {
    if (body === null || typeof body !== "object" || Array.isArray(body)) {
        return {
            ok: false,
            code: "INVALID_JSON_BODY",
            message: "Request body must be a JSON object with a \"prompt\" field.",
        };
    }

    const prompt = /** @type {{ prompt?: unknown }} */ (body).prompt;
    if (typeof prompt !== "string") {
        return {
            ok: false,
            code: "INVALID_PROMPT",
            message: "The \"prompt\" field must be a non-empty string.",
        };
    }

    const trimmed = prompt.trim();
    if (!trimmed) {
        return {
            ok: false,
            code: "EMPTY_PROMPT",
            message: "The \"prompt\" field cannot be empty.",
        };
    }

    if (trimmed.length > MAX_PROMPT_CHARS) {
        return {
            ok: false,
            code: "PROMPT_TOO_LONG",
            message: `The "prompt" field must be at most ${MAX_PROMPT_CHARS} characters.`,
        };
    }

    return { ok: true, prompt: trimmed };
}