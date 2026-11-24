import { GoogleGenAI } from "@google/genai";
import { DEFAULT_MODEL } from "./config.mjs";

/** @type {GoogleGenAI | null} */
let client = null;

function normalizeEnvValue(value) {
    if (!value || typeof value !== "string") {
        return "";
    }
    return value.trim().replace(/^['"]|['"]$/g, "");
}

function getApiKey() {
    const key = normalizeEnvValue(process.env.GEMINI_API_KEY);
    if (!key) {
        return null;
    }
    return key;
}

export function assertGeminiConfigured() {
    if (!getApiKey()) {
        const err = new Error("Gemini API key is not configured");
        err.code = "CONFIG_MISSING_API_KEY";
        throw err;
    }
}

function getClient() {
    assertGeminiConfigured();
    if (!client) {
        client = new GoogleGenAI({ apiKey: getApiKey() });
    }
    return client;
}

export function getModelName() {
    const fromEnv = normalizeEnvValue(process.env.GEMINI_MODEL);
    if (fromEnv) {
        return fromEnv;
    }
    return DEFAULT_MODEL;
}

/**
 * @param {string} prompt
 * @returns {Promise<string>}
 */
export async function generateText(prompt) {
    const ai = getClient();
    const model = getModelName();
    const response = await ai.models.generateContent({
        model,
        contents: prompt,
    });
    return typeof response.text === "string" ? response.text : "";
}