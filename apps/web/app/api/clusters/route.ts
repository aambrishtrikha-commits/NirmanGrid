import { allClusters, getCluster } from "../../../lib/store";
import type { TenantId } from "../../../../../packages/schema/src";

export const dynamic = "force-dynamic";

export function GET(req: Request) {
  const url = new URL(req.url);
  const id = url.searchParams.get("id");
  if (id) {
    const cluster = getCluster(id);
    if (!cluster) return Response.json({ error: "not found" }, { status: 404 });
    return Response.json({ cluster });
  }
  const tenant = url.searchParams.get("tenant") as TenantId | null;
  return Response.json({ clusters: allClusters(tenant || undefined) });
}
