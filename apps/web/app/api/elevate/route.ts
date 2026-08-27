import { geminiReady, writeMinistryNote } from "../../../lib/gemini";
import { elevateCluster, getCluster } from "../../../lib/store";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

export async function POST(req: Request) {
  const { cluster_id } = (await req.json()) as { cluster_id?: string };
  if (!cluster_id) {
    return Response.json({ error: "cluster_id required" }, { status: 400 });
  }
  const cluster = getCluster(cluster_id);
  if (!cluster) return Response.json({ error: "not found" }, { status: 404 });
  if (!geminiReady()) {
    return Response.json(
      { error: "GEMINI_API_KEY is not set. Ministry note cannot be written." },
      { status: 503 },
    );
  }
  const note = await writeMinistryNote(cluster);
  const updated = elevateCluster(cluster_id, note);
  return Response.json({
    cluster: updated,
    ministry_note: note,
    citizen_update:
      "Demand elevated to planning shelf — not merely registered.",
  });
}
