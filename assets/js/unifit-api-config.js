/* Local dev: empty base → meta tag or localhost fallback in gemini-api.js.
   Netlify build overwrites dist/assets/js/unifit-api-config.js from UNIFIT_API_BASE. */
(function (root) {
    root.__UNIFIT_API_BASE__ = "";
})(typeof globalThis !== "undefined" ? globalThis : typeof window !== "undefined" ? window : this);