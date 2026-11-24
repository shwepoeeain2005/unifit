/**
 * Proxies Ask UniFit to Render using UNIFIT_API_BASE (Vercel runtime env).
 * Browser calls same-origin /api/assistant/chat — no API keys in the frontend.
 */
export const config = {
    matcher: "/api/assistant/chat",
};

function jsonResponse(status, body) {
    return new Response(JSON.stringify(body), {
        status,
        headers: { "content-type": "application/json; charset=utf-8" },
    });
}

export default async function middleware(request) {
  if (request.method === "OPTIONS") {
      return new Response(null, {
          status: 204,
          headers: {
              "access-control-allow-methods": "POST, OPTIONS",
              "access-control-allow-headers": "content-type",
          },
      });
  }

  if (request.method !== "POST") {
      return jsonResponse(405, {
          error: "Method not allowed. Use POST.",
          code: "METHOD_NOT_ALLOWED",
      });
  }

  const base = (process.env.UNIFIT_API_BASE || "").trim().replace(/\/$/, "");
  if (!base) {
      return jsonResponse(503, {
          error: "The assistant API is not configured for this site.",
          code: "API_BASE_MISSING",
      });
  }

  const target = `${base}/api/assistant/chat`;
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("connection");

  const body = await request.arrayBuffer();

  try {
      const upstream = await fetch(target, {
          method: "POST",
          headers,
          body,
      });
      const text = await upstream.text();
      return new Response(text, {
          status: upstream.status,
          headers: { "content-type": "application/json; charset=utf-8" },
      });
  } catch {
      return jsonResponse(502, {
          error: "Could not reach the assistant service.",
          code: "NETWORK_ERROR",
      });
  }
}