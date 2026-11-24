/**
 * Map OpenRouter / upstream errors to safe client messages.
 * @param {unknown} err
 * @returns {{ httpStatus: number, code: string, error: string }}
 */
export function mapOpenRouterError(err) {
    let apiMessage = "";
    let httpStatus = 502;

    if (err && typeof err === "object") {
        if ("status" in err && Number.isFinite(Number(err.status))) {
            httpStatus = Number(err.status);
        }
        if ("message" in err && typeof err.message === "string") {
            apiMessage = err.message;
        }
        if ("error" in err && err.error && typeof err.error === "object") {
            const nested = err.error;
            if ("message" in nested && typeof nested.message === "string") {
                apiMessage = nested.message;
            }
        }
    }

    const lower = apiMessage.toLowerCase();

    if (
        lower.includes("incorrect api key")
        || lower.includes("invalid api key")
        || lower.includes("invalid_api_key")
        || httpStatus === 401
    ) {
        return {
            httpStatus: 401,
            code: "INVALID_API_KEY",
            error: "The assistant service could not authenticate. Please try again later.",
        };
    }

    if (lower.includes("model") && (lower.includes("not found") || lower.includes("does not exist") || lower.includes("access"))) {
        return {
            httpStatus: 400,
            code: "MODEL_NOT_FOUND",
            error: "The configured assistant model is not available. Check OPENROUTER_MODEL in .env.",
        };
    }

    if (httpStatus === 429 || lower.includes("rate limit") || lower.includes("too many requests")) {
        return {
            httpStatus: 429,
            code: "RATE_LIMITED",
            error: "Too many requests. Please wait a moment and try again.",
        };
    }

    if (err && typeof err === "object") {
        const code = "code" in err ? String(err.code) : "";
        if (
            code === "ECONNREFUSED"
            || code === "ENOTFOUND"
            || code === "ETIMEDOUT"
            || code === "ECONNRESET"
            || lower.includes("fetch failed")
            || lower.includes("network")
        ) {
            return {
                httpStatus: 502,
                code: "NETWORK_ERROR",
                error: "Could not reach the assistant service. Check your connection and try again.",
            };
        }
    }

    return {
        httpStatus: httpStatus >= 400 && httpStatus < 600 ? httpStatus : 502,
        code: "AI_SERVICE_UNAVAILABLE",
        error: "The assistant is unavailable right now. Please try again later.",
    };
}