from datetime import datetime, timezone

from nirmangrid.sample_events import delhi_sample_tickets
from nirmangrid.schemas import Classification, Ticket
from nirmangrid.score import WEIGHTS, score_cluster, to_cluster


def _ticket(kind: str, district: str = "New Delhi", n: int = 1, month: int = 8) -> Ticket:
    created = datetime(2026, month, 20, 6, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    return Ticket(
        id=f"t-{n}",
        tenant_id="delhi_pwd",
        lat=28.61,
        lng=77.21,
        text="test",
        lang="en",
        classification=Classification(
            type=kind,  # type: ignore[arg-type]
            severity="medium",
            lang="en",
            summary="test",
            reason="test",
            confidence=0.9,
            mplads_eligible=True,
        ),
        cluster_id="c1",
        source="SAMPLE",
        district=district,
        created_at=created,
    )


def test_weights_sum_to_one():
    assert round(sum(WEIGHTS.values()), 2) == 1.0


def test_sample_count_is_sixty():
    tickets = delhi_sample_tickets()
    assert len(tickets) == 60
    assert all(t.source == "SAMPLE" for t in tickets)


def test_nine_reporters_repeat_component():
    tickets = [_ticket("pothole", n=i) for i in range(9)]
    breakdown = score_cluster(tickets)
    repeat = next(c for c in breakdown.components if c.key == "repeat")
    assert repeat.value == 9 / 12
    assert breakdown.mode == "partial"


def test_monsoon_boosts_drainage_not_streetlight():
    drain = score_cluster([_ticket("drainage", month=8)])
    light = score_cluster([_ticket("streetlight", month=8)])
    drain_s = next(c for c in drain.components if c.key == "seasonal")
    light_s = next(c for c in light.components if c.key == "seasonal")
    assert drain_s.value == 1.0
    assert light_s.value == 0.0
    assert drain.priority_score > light.priority_score


def test_census_vintage_labelled():
    breakdown = score_cluster([_ticket("pothole", "South Delhi")])
    pop = next(c for c in breakdown.components if c.key == "population")
    assert "2011" in pop.note
    assert any("2011" in n for n in breakdown.vintage_notes)


def test_gemini_does_not_own_the_score():
    cluster = to_cluster("x", [_ticket("pothole", n=i) for i in range(3)])
    dumped = cluster.model_dump()
    assert "priority_score" in dumped["score"]
    assert dumped["tickets"][0]["classification"].get("priority_score") is None
