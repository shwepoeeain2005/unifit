/** Build the public site and configure its Netlify routes to Render. */
import { writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const chatOrigin = process.env.UNIFIT_CHAT_API_BASE?.trim();
let chatUrl;
if (chatOrigin) {
    chatUrl = new URL(chatOrigin);
    if (chatUrl.protocol !== "https:" || chatUrl.username || chatUrl.password ||
        chatUrl.pathname !== "/" || chatUrl.search || chatUrl.hash) {
        throw new Error("UNIFIT_CHAT_API_BASE must be a public HTTPS origin");
    }
}

function runScript(name, env = process.env) {
    const script = fileURLToPath(new URL(name, import.meta.url));
    const result = spawnSync(process.execPath, [script], { env, stdio: "inherit" });
    if (result.error) throw result.error;
    if (result.status !== 0) process.exit(result.status ?? 1);
}

runScript("./build-public.mjs");
runScript("./write-unifit-api-config.mjs", {
    ...process.env,
    UNIFIT_API_CONFIG_OUT: "dist/assets/js/unifit-api-config.js",
});

if (chatUrl) {
    writeFileSync(new URL("../dist/_redirects", import.meta.url),
        `/api/chat ${chatUrl.origin}/api/chat 200\n`, "utf8");
}
