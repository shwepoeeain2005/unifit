/** Maximum JSON request body size (bytes). */
export const MAX_BODY_BYTES = 16 * 1024;

/** Maximum prompt length after trim (characters). */
export const MAX_PROMPT_CHARS = 8_000;

export const DEFAULT_MODEL = "gemini-3.5-flash-lite";

export const GEMINI_GENERATE_PATH = "/api/gemini/generate";

export const ASSISTANT_CHAT_PATH = "/api/assistant/chat";

export const DEFAULT_PORT = 3001;
export const DEFAULT_BIND = "127.0.0.1";

/** Origins allowed for browser calls from the static preview server. */
export const DEFAULT_CORS_ORIGINS = [
    "http://127.0.0.1:8082",
    "http://localhost:8082",
];