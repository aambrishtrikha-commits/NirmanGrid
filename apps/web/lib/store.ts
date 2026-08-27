import { toCluster } from "../../../packages/score/src";
import type { Cluster, TenantId, Ticket } from "../../../packages/schema/src";
import { clusterRadiusMeters, haversineMeters } from "../../../packages/score/src";
import { delhiSampleTickets } from "./sampleEvents";
import { districtForPoint } from "./tenants";

const tickets = new Map<string, Ticket>();

function seed(): void {
  if (tickets.size > 0) return;
  for (const t of delhiSampleTickets()) tickets.set(t.id, t);
}

export function allTickets(tenant?: TenantId): Ticket[] {
  seed();
  const rows = [...tickets.values()].sort(
    (a, b) => +new Date(b.created_at) - +new Date(a.created_at),
  );
  return tenant ? rows.filter((t) => t.tenant_id === tenant) : rows;
}

export function getTicket(id: string): Ticket | undefined {
  seed();
  return tickets.get(id);
}

export function addTicket(ticket: Ticket): Ticket {
  seed();
  tickets.set(ticket.id, ticket);
  return ticket;
}

export function updateTicket(
  id: string,
  patch: Partial<Ticket>,
): Ticket | undefined {
  seed();
  const current = tickets.get(id);
  if (!current) return undefined;
  const next = { ...current, ...patch };
  tickets.set(id, next);
  return next;
}

export function assignClusterId(ticket: Ticket): string {
  seed();
  const radius = clusterRadiusMeters(ticket.tenant_id);
  let best: { id: string; d: number } | null = null;
  for (const other of tickets.values()) {
    if (other.tenant_id !== ticket.tenant_id) continue;
    if (other.classification.type !== ticket.classification.type) continue;
    const d = haversineMeters(ticket, other);
    if (d <= radius && (!best || d < best.d)) {
      best = { id: other.cluster_id, d };
    }
  }
  return best?.id ?? `${ticket.tenant_id}-${ticket.classification.type}-${Date.now()}`;
}

export function allClusters(tenant?: TenantId): Cluster[] {
  const grouped = new Map<string, Ticket[]>();
  for (const t of allTickets(tenant)) {
    const list = grouped.get(t.cluster_id) ?? [];
    list.push(t);
    grouped.set(t.cluster_id, list);
  }
  return [...grouped.entries()]
    .map(([id, list]) => toCluster(id, list))
    .sort((a, b) => b.score.priority_score - a.score.priority_score);
}

export function getCluster(id: string): Cluster | undefined {
  return allClusters().find((c) => c.id === id);
}

export function elevateCluster(id: string, note: string): Cluster | undefined {
  const cluster = getCluster(id);
  if (!cluster) return undefined;
  for (const t of cluster.tickets) {
    updateTicket(t.id, { status: "elevated", ministry_note: note });
  }
  return getCluster(id);
}

export function newTicketId(): string {
  seed();
  return `NG-${Date.now().toString(36).toUpperCase()}`;
}

export { districtForPoint };
