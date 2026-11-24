/**
 * Server-side OpenRouter configuration (no secrets in logs).
 * Loaded via server/load-env.mjs before routes run.
 */

export function normalizeEnvValue(value) {
    if (!value || typeof value !== "string") {
        return "";
    }
    return value.trim().replace(/^['"]|['"]$/g, "");
}

export function getOpenRouterApiKey() {
    return normalizeEnvValue(process.env.OPENROUTER_API_KEY);
}

export function getOpenRouterModelName() {
    return normalizeEnvValue(process.env.OPENROUTER_MODEL);
}

export function isOpenRouterConfigured() {
    return Boolean(getOpenRouterApiKey() && getOpenRouterModelName());
}

export function assertOpenRouterConfigured() {
    if (!getOpenRouterApiKey()) {
        const err = new Error("OpenRouter API key is not configured");
        err.code = "CONFIG_MISSING_API_KEY";
        throw err;
    }
    if (!getOpenRouterModelName()) {
        const err = new Error("OpenRouter model is not configured");
        err.code = "CONFIG_MISSING_MODEL";
        throw err;
    }
}