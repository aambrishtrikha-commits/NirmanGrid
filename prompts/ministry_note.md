# NirmanGrid ministry note

Write a 12-line note for a national planner (MoHUA / MoRTH / NITI-style desk).

You are given JSON: cluster location, demand type, SAMPLE reporter count, and the SQL `priority_score` breakdown with weights and vintage notes.

## Rules

- Exactly 12 short lines. No title block. No markdown.
- Line 1: what the work is and where (district, state, tenant).
- Line 2: citizen demand in one sentence. State that events are SAMPLE if `source=SAMPLE`.
- Line 3: SQL priority_score and score mode (`full` or `partial`).
- Lines 4–9: one line per score component, using the provided numbers. Do not change them.
- Line 10: Census vintage. If population used Census 2011, say 2011.
- Line 11: what is already funded nearby, or that no MPLADS/PMGSY work of this class is in the snapshot.
- Line 12: recommended next step for a plan cell. Not a sanction. Not a claim that PWD has signed anything.

If your prose would disagree with the SQL score, keep the SQL number and write: "SQL score stands; this note does not override it."

Do not invent Gati Shakti project IDs, contractor names, or live Sewa ticket numbers.
