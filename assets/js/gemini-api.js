/**
 * Browser client for the UniFit AI backend (UniFit Node server only — never third-party APIs).
 * Attaches to window.unifitGemini in the browser.
 */
(function (root, factory) {
    if (typeof module === "object" && module.exports) {
        module.exports = factory();
    } else {
        root.unifitGemini = factory();
    }
}(typeof globalThis !== "undefined" ? globalThis : this, function () {
    const DEFAULT_CHAT_PATH = "/api/assistant/chat";
    let activeRequest = null;

    function resolveChatPath() {
        const meta = document.querySelector('meta[name="unifit-api-generate-path"]');
        const fromMeta = meta && meta.getAttribute("content");
        if (fromMeta && fromMeta.trim()) {
            const path = fromMeta.trim();
            return path.startsWith("/") ? path : `/${path}`;
        }
        return DEFAULT_CHAT_PATH;
    }

    /**
     * Local dev: absolute URL to the Node API. Production: same-origin relative path
     * (Vercel rewrite → Render). No UNIFIT_API_BASE in the browser.
     */
    function resolveRequestUrl() {
        const chatPath = resolveChatPath();
        if (typeof window === "undefined") {
            return chatPath;
        }
        const host = window.location.hostname;
        if (host === "127.0.0.1" || host === "localhost") {
            return `http://127.0.0.1:3001${chatPath}`;
        }
        return chatPath;
    }

    function resolveApiBase() {
        const requestUrl = resolveRequestUrl();
        if (requestUrl.startsWith("/")) {
            return "";
        }
        try {
            const url = new URL(requestUrl);
            return url.origin;
        } catch {
            return "";
        }
    }

    function friendlyServerError(data) {
        const code = data.code || "";
        if (code === "RATE_LIMITED") {
            return "Too many requests. Please wait a moment and try again.";
        }
        if (code === "NETWORK_ERROR") {
            return "Could not reach the assistant. Check your connection and try again.";
        }
        if (code === "AI_SERVICE_UNAVAILABLE" || code === "CONFIG_MISSING_API_KEY" || code === "CONFIG_MISSING_MODEL") {
            return "The assistant is not available right now. Please try again later.";
        }
        if (typeof data.error === "string" && data.error.trim()) {
            return data.error;
        }
        return "The assistant could not answer right now.";
    }

    /**
     * @param {string} message
     * @param {Record<string, unknown> | null | undefined} [searchContext]
     * @returns {Promise<{ ok: true, text: string } | { ok: false, error: string, code?: string }>}
     */
    async function chat(message, searchContext) {
        const trimmed = typeof message === "string" ? message.trim() : "";
        if (!trimmed) {
            return {
                ok: false,
                error: "Please enter a question.",
                code: "EMPTY_MESSAGE",
            };
        }

        if (activeRequest) {
            return {
                ok: false,
                error: "Please wait for the current question to finish.",
                code: "IN_FLIGHT",
            };
        }

        const payload = { message: trimmed };
        if (searchContext && typeof searchContext === "object" && Object.keys(searchContext).length > 0) {
            payload.searchContext = searchContext;
        }

        const requestUrl = resolveRequestUrl();

        activeRequest = (async () => {
            try {
                const response = await fetch(requestUrl, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });

                let data = {};
                try {
                    data = await response.json();
                } catch {
                    data = {
                        error: "Unexpected response from the server.",
                        code: "INVALID_RESPONSE",
                    };
                }

                if (!response.ok) {
                    return {
                        ok: false,
                        error: friendlyServerError(data),
                        code: data.code || "REQUEST_FAILED",
                    };
                }

                const reply = typeof data.reply === "string"
                    ? data.reply
                    : (typeof data.text === "string" ? data.text : "");

                return {
                    ok: true,
                    text: reply,
                };
            } catch {
                return {
                    ok: false,
                    error: "Could not reach the assistant. Make sure the API server is running.",
                    code: "NETWORK_ERROR",
                };
            } finally {
                activeRequest = null;
            }
        })();

        return activeRequest;
    }

    function isLoading() {
        return Boolean(activeRequest);
    }

    return {
        chat,
        generate: chat,
        isLoading,
        resolveApiBase,
        resolveChatPath,
        resolveGeneratePath: resolveChatPath,
        resolveRequestUrl,
    };
}));