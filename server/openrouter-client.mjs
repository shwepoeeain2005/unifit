import OpenAI from "openai";
import {
    assertOpenRouterConfigured,
    getOpenRouterApiKey,
    getOpenRouterModelName,
    normalizeEnvValue,
} from "./openrouter-env.mjs";

/** @type {OpenAI | null} */
let client = null;

const OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1";

function getClient() {
    assertOpenRouterConfigured();
    if (!client) {
        const siteUrl = normalizeEnvValue(process.env.OPENROUTER_SITE_URL) || "http://127.0.0.1:8082";
        client = new OpenAI({
            apiKey: getOpenRouterApiKey(),
            baseURL: OPENROUTER_BASE_URL,
            defaultHeaders: {
                "HTTP-Referer": siteUrl,
                "X-Title": "UniFit",
            },
        });
    }
    return client;
}

const SYSTEM_PROMPT = `You are UniFit's University Recommendation Assistant for Myanmar matriculation students.
Use the verified UniFit search context when provided. It comes from published 2026 admission rules in the UniFit app.
Be concise, supportive, and practical. If context is missing, answer generally about subject sets and how to use UniFit search.
Always remind students to confirm final admission rules with the university.`;

/**
 * @param {string} message
 * @param {Record<string, unknown> | null | undefined} searchContext
 * @returns {Promise<string>}
 */
export async function completeAssistantChat(message, searchContext) {
    const openrouter = getClient();
    const model = getOpenRouterModelName();

    let userContent = message;
    if (searchContext && typeof searchContext === "object" && Object.keys(searchContext).length > 0) {
        userContent += `\n\nUniFit verified search context (JSON):\n${JSON.stringify(searchContext)}`;
    }

    const response = await openrouter.chat.completions.create({
        model,
        messages: [
            { role: "system", content: SYSTEM_PROMPT },
            { role: "user", content: userContent },
        ],
    });

    const text = response.choices?.[0]?.message?.content;
    return typeof text === "string" ? text : "";
}