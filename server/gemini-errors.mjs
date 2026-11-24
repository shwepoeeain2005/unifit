/**
 * Map SDK / API errors to safe client messages (no secrets or stack traces).
 * @param {unknown} err
 * @returns {{ httpStatus: number, code: string, error: string }}
 */
export function mapGeminiError(err) {
    let apiMessage = "";
    let httpStatus = 502;

    if (err && typeof err === "object") {
        if ("status" in err && Number.isFinite(Number(err.status))) {
            httpStatus = Number(err.status);
        }
        const raw = "message" in err ? String(err.message) : "";
        const jsonStart = raw.indexOf("{");
        if (jsonStart >= 0) {
            try {
                const parsed = JSON.parse(raw.slice(jsonStart));
                const nested = parsed?.error?.message;
                if (typeof nested === "string") {
                    apiMessage = nested;
                }
            } catch {
                apiMessage = raw;
            }
        } else {
            apiMessage = raw;
        }
    }

    const lower = apiMessage.toLowerCase();

    if (lower.includes("user location is not supported") || lower.includes("location is not supported")) {
        return {
            httpStatus: 403,
            code: "REGION_NOT_SUPPORTED",
            error:
                "Google's Gemini API is not available from your current region or network. "
                + "Use a supported region (for example via VPN), host the API server in a supported country, "
                + "or check Google AI Studio availability for your location.",
        };
    }

    if (
        lower.includes("api key not valid")
        || lower.includes("api_key_invalid")
        || lower.includes("invalid api key")
        || httpStatus === 401
    ) {
        return {
            httpStatus: 401,
            code: "INVALID_API_KEY",
            error:
                "The server API key was rejected. Create a key at Google AI Studio (usually starts with AIza…) "
                + "and set GEMINI_API_KEY in .env with no extra spaces or quotes.",
        };
    }

    if (lower.includes("not found") && (lower.includes("model") || lower.includes("models"))) {
        return {
            httpStatus: 400,
            code: "MODEL_NOT_FOUND",
            error:
                "The configured GEMINI_MODEL is not available for this API key. "
                + "Try gemini-2.5-flash or another model listed in Google AI Studio.",
        };
    }

    if (httpStatus === 429 || lower.includes("quota") || lower.includes("rate limit")) {
        return {
            httpStatus: 429,
            code: "RATE_LIMITED",
            error: "Gemini rate limit reached. Wait a moment and try again.",
        };
    }

    return {
        httpStatus: httpStatus >= 400 && httpStatus < 600 ? httpStatus : 502,
        code: "GEMINI_UNAVAILABLE",
        error: "Unable to complete the Gemini request. Please try again later.",
    };
}