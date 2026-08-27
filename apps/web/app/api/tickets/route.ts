import { allTickets } from "../../../lib/store";
import type { TenantId } from "../../../../../packages/schema/src";

export const dynamic = "force-dynamic";

export function GET(req: Request) {
  const url = new URL(req.url);
  const tenant = url.searchParams.get("tenant") as TenantId | null;
  const tickets = allTickets(tenant || undefined).map((t) => ({
    ...t,
    photo_sha256: t.photo_sha256 ? "redacted" : undefined,
  }));
  return Response.json({ tickets, sample_banner: true });
}
