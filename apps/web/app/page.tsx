import Link from "next/link";

export default function Home() {
  return (
    <main className="page">
      <p className="kicker">Track 1 · Digital Public Infrastructure</p>
      <h1>Citizens speak a development need. The system ranks it against what India is already funded to build.</h1>
      <p className="lede">
        NirmanGrid is a Digital Public Good. Field intake is not enough.
        Every cluster is scored on Census 2011, road gap, and public investment
        already present, then ranked for a national desk. PWD Delhi and PWD
        Rajasthan share one protocol.
      </p>
      <div className="actions">
        <Link className="btn terra" href="/citizen">
          File a demand
        </Link>
        <Link className="btn secondary" href="/ops">
          Open the planning desk
        </Link>
      </div>
      <section className="grid-3">
        <article className="card">
          <p className="kicker">01 Field</p>
          <h2>Citizen + engineer</h2>
          <p>Photo, pin, voice or text. Gemini classifies. Ticket in under a minute. SLA clock. WhatsApp later; this web form is the judge path.</p>
        </article>
        <article className="card">
          <p className="kicker">02 Planning</p>
          <h2>SQL score, not a vibe</h2>
          <p>Repeat demand 25% · population 20% · vulnerability 10% · gap 20% · existing investment 15% · season 10%. Gemini does not invent this number.</p>
        </article>
        <article className="card">
          <p className="kicker">03 National</p>
          <h2>Ranked shelf</h2>
          <p>Two tenants, one code path. 12-line ministry note written from the score JSON. If Gemini and SQL disagree, SQL wins.</p>
        </article>
      </section>
      <section className="grid-2" style={{ marginTop: 16 }}>
        <article className="card">
          <p className="kicker">Honesty</p>
          <h2>What this map is not</h2>
          <p>
            Events are stamped SAMPLE. Census figures are 2011 PCA. There is no
            signed PWD work order and no live Gati Shakti join. We sit on top of
            Sewa; we do not replace it.
          </p>
        </article>
        <article className="card">
          <p className="kicker">Google AI</p>
          <h2>Two jobs, two tools</h2>
          <p>
            Gemini sees the photo and writes the note. BigQuery/SQL scores the
            cluster. They are not allowed to swap jobs. Set <code>GEMINI_API_KEY</code> before filing a live report.
          </p>
        </article>
      </section>
    </main>
  );
}
