from __future__ import annotations

import time
from collections import defaultdict

from .sample_events import delhi_sample_tickets
from .schemas import Cluster, TenantId, Ticket
from .score import cluster_radius_meters, haversine_meters, to_cluster
from .tenants import district_for_point

_tickets: dict[str, Ticket] = {}


def seed() -> None:
    if _tickets:
        return
    for ticket in delhi_sample_tickets():
        _tickets[ticket.id] = ticket


def all_tickets(tenant: TenantId | None = None) -> list[Ticket]:
    seed()
    rows = sorted(_tickets.values(), key=lambda t: t.created_at, reverse=True)
    if tenant:
        rows = [t for t in rows if t.tenant_id == tenant]
    return rows


def add_ticket(ticket: Ticket) -> Ticket:
    seed()
    _tickets[ticket.id] = ticket
    return ticket


def get_ticket(ticket_id: str) -> Ticket | None:
    seed()
    return _tickets.get(ticket_id)


def assign_cluster_id(ticket: Ticket) -> str:
    seed()
    radius = cluster_radius_meters(ticket.tenant_id)
    best: tuple[str, float] | None = None
    point = {"lat": ticket.lat, "lng": ticket.lng}
    for other in _tickets.values():
        if other.tenant_id != ticket.tenant_id:
            continue
        if other.classification.type != ticket.classification.type:
            continue
        dist = haversine_meters(point, {"lat": other.lat, "lng": other.lng})
        if dist <= radius and (best is None or dist < best[1]):
            best = (other.cluster_id, dist)
    if best:
        return best[0]
    return f"{ticket.tenant_id}-{ticket.classification.type}-{int(time.time() * 1000)}"


def all_clusters(tenant: TenantId | None = None) -> list[Cluster]:
    grouped: dict[str, list[Ticket]] = defaultdict(list)
    for ticket in all_tickets(tenant):
        grouped[ticket.cluster_id].append(ticket)
    clusters = [to_cluster(cid, rows) for cid, rows in grouped.items()]
    return sorted(clusters, key=lambda c: c.score.priority_score, reverse=True)


def get_cluster(cluster_id: str) -> Cluster | None:
    return next((c for c in all_clusters() if c.id == cluster_id), None)


def elevate_cluster(cluster_id: str, note: str) -> Cluster | None:
    cluster = get_cluster(cluster_id)
    if not cluster:
        return None
    for ticket in cluster.tickets:
        updated = ticket.model_copy(update={"status": "elevated", "ministry_note": note})
        _tickets[ticket.id] = updated
    return get_cluster(cluster_id)


def new_ticket_id() -> str:
    return f"NG-{int(time.time() * 1000):X}"


__all__ = [
    "add_ticket",
    "all_clusters",
    "all_tickets",
    "assign_cluster_id",
    "district_for_point",
    "elevate_cluster",
    "get_cluster",
    "new_ticket_id",
]
