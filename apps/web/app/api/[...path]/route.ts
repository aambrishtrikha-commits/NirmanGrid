const API = process.env.API_URL || "http://127.0.0.1:8000";

async function proxy(req: Request, path: string[]) {
  const incoming = new URL(req.url);
  const target = `${API}/api/${path.join("/")}${incoming.search}`;
  const init: RequestInit = { method: req.method, cache: "no-store" };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
    init.headers = {
      "content-type": req.headers.get("content-type") || "application/json",
    };
  }
  const res = await fetch(target, init);
  return new Response(await res.text(), {
    status: res.status,
    headers: {
      "content-type": res.headers.get("content-type") || "application/json",
    },
  });
}

export async function GET(
  req: Request,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function POST(
  req: Request,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export const dynamic = "force-dynamic";
export const maxDuration = 60;
