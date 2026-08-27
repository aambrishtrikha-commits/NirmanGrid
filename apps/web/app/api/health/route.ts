import { geminiReady } from "../../../lib/gemini";
import { allTickets } from "../../../lib/store";

export const dynamic = "force-dynamic";

export function GET() {
  const tickets = allTickets();
  return Response.json({
    ok: true,
    service: "nirmangrid",
    gemini: geminiReady(),
    sample_events: tickets.filter((t) => t.source === "SAMPLE").length,
    live_events: tickets.filter((t) => t.source === "LIVE_WEB").length,
  });
}
