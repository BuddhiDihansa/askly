"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, BrainCircuit, MessageCircle, Upload } from "lucide-react";
import Sidebar from "../../components/Sidebar";
import Guard from "../../components/Guard";
import Orb3D from "../../components/Orb3D";
import { api } from "../../lib/api";

export default function Dashboard() {
  const [me, setMe] = useState<any>(null);
  const [p, setP] = useState<any>({ stats: {}, mastery: [] });

  useEffect(() => {
    api("/api/auth/me").then(setMe).catch(() => {});
    api("/api/progress").then(setP).catch(() => {});
  }, []);

  return (
    <Guard>
      <div className="shell">
        <Sidebar />
        <main className="main">
          <div className="top">
            <div>
              <p className="eyebrow">Personal learning cockpit</p>
              <h1 className="title">Good to see you, {me?.name?.split(" ")[0] || "student"}.</h1>
              <p className="subtitle">Your study space for documents, AI tutoring, adaptive quizzes and measurable progress.</p>
            </div>
            <Link className="btn" href="/chat">Ask ASKLY <ArrowRight size={16} style={{ verticalAlign: "-3px" }} /></Link>
          </div>

          <section className="card hero-card">
            <div className="hero-copy">
              <p className="eyebrow">Your AI study partner</p>
              <h2>Learn faster. Understand deeper. Keep your progress.</h2>
              <p>Upload your material, ask questions with context, then use adaptive quizzes to turn understanding into lasting mastery.</p>
              <div className="hero-actions">
                <Link className="btn" href="/documents"><Upload size={16} style={{ verticalAlign: "-3px" }} /> Add material</Link>
                <Link className="btn secondary" href="/quiz"><BrainCircuit size={16} style={{ verticalAlign: "-3px" }} /> Practice</Link>
              </div>
            </div>
            <div className="hero-orb"><Orb3D /></div>
          </section>

          <div className="grid cards">
            <div className="card"><div className="label">Documents</div><div className="stat">{p.stats?.documents || 0}</div></div>
            <div className="card"><div className="label">Conversations</div><div className="stat">{p.stats?.conversations || 0}</div></div>
            <div className="card"><div className="label">Completed quizzes</div><div className="stat">{p.stats?.quizzes || 0}</div></div>
            <div className="card"><div className="label">Topics tracked</div><div className="stat">{p.mastery?.length || 0}</div></div>
            <div className="card"><div className="label">Cards due</div><div className="stat">{p.stats?.due_flashcards || 0}</div></div>
          </div>

          <div className="grid" style={{ gridTemplateColumns: "1.2fr .8fr", marginTop: 18 }}>
            <div className="card">
              <div className="section-head"><h2>Jump back in</h2></div>
              <div className="grid quick-grid">
                <Link className="card quick-card" href="/chat">
                  <span className="quick-icon"><MessageCircle size={19} /></span>
                  <div><b>Ask your tutor</b><p className="muted" style={{ margin: "5px 0 0", fontSize: 12 }}>Explain a concept or explore a question.</p></div>
                </Link>
                <Link className="card quick-card" href="/documents">
                  <span className="quick-icon"><BookOpen size={19} /></span>
                  <div><b>Open study material</b><p className="muted" style={{ margin: "5px 0 0", fontSize: 12 }}>Keep your learning context in one place.</p></div>
                </Link>
                <Link className="card quick-card" href="/quiz">
                  <span className="quick-icon"><BrainCircuit size={19} /></span>
                  <div><b>Practice a topic</b><p className="muted" style={{ margin: "5px 0 0", fontSize: 12 }}>Generate an adaptive five-question quiz.</p></div>
                </Link>
              </div>
            </div>

            <div className="card">
              <div className="section-head"><h2>Mastery snapshot</h2><Link className="muted" href="/progress">View all →</Link></div>
              {p.mastery?.slice(0, 5).map((m: any) => (
                <div className="progress-row" key={m.topic}>
                  <div className="row"><span>{m.topic}</span><span className="muted">{Math.round(m.mastery * 100)}%</span></div>
                  <div className="bar"><i style={{ width: `${m.mastery * 100}%` }} /></div>
                </div>
              ))}
              {!p.mastery?.length && <div className="empty-state">Complete a quiz to start tracking mastery.</div>}
              {p.weak_topics?.length > 0 && <p className="muted" style={{ marginTop: 16, fontSize: 12 }}>Focus next: {p.weak_topics.slice(0, 3).join(", ")}</p>}
            </div>
          </div>
        </main>
      </div>
    </Guard>
  );
}
