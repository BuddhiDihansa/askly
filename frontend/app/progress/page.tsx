"use client";

import { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Guard from "../../components/Guard";
import { api } from "../../lib/api";

export default function Progress() {
  const [p, setP] = useState<any>({ mastery: [], stats: {} });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api("/api/progress").then(setP).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <Guard>
      <div className="shell">
        <Sidebar />
        <main className="main">
          <div className="top">
            <div>
              <p className="eyebrow">Learning analytics</p>
              <h1 className="title">Your progress</h1>
              <p className="subtitle">A clear view of activity and topic mastery from your quiz performance.</p>
            </div>
          </div>

          <div className="grid cards">
            {Object.entries(p.stats || {}).map(([k, v]: any) => (
              <div className="card" key={k}><div className="label">{k}</div><div className="stat">{v}</div></div>
            ))}
          </div>

          <div className="card" style={{ marginTop: 18 }}>
            <div className="section-head">
              <div><h2>Topic mastery</h2><p className="muted" style={{ margin: "6px 0 0", fontSize: 12 }}>Complete more quizzes to refine these estimates.</p></div>
            </div>
            {loading && <p className="loading muted">Loading progress…</p>}
            {!loading && !p.mastery?.length && <div className="empty-state">No mastery data yet. Head to Adaptive Quiz and practice your first topic.</div>}
            {p.mastery?.map((m: any) => (
              <div className="progress-row" key={m.topic} style={{ margin: "22px 0" }}>
                <div className="row"><b>{m.topic}</b><span className="muted">{Math.round(m.mastery * 100)}%</span></div>
                <div className="bar"><i style={{ width: `${Math.max(0, Math.min(100, m.mastery * 100))}%` }} /></div>
              </div>
            ))}
          </div>
        </main>
      </div>
    </Guard>
  );
}
