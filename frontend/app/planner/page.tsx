"use client";

import { useEffect, useState } from "react";
import { CalendarDays, Sparkles } from "lucide-react";
import Guard from "../../components/Guard";
import Sidebar from "../../components/Sidebar";
import { api } from "../../lib/api";

export default function Planner() {
  const [plan, setPlan] = useState<any>({ tasks: [] });
  const [days, setDays] = useState(7);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { api("/api/planner").then(setPlan).catch(() => {}); }, []);
  async function create() { setBusy(true); setError(""); try { setPlan(await api("/api/planner", { method: "POST", body: JSON.stringify({ days }) })); } catch (err: any) { setError(err.message); } finally { setBusy(false); } }
  return <Guard><div className="shell"><Sidebar /><main className="main"><div className="top"><div><p className="eyebrow">Personal rhythm</p><h1 className="title">Study planner</h1><p className="subtitle">A simple daily plan prioritizing your weakest topics and your available study time.</p></div></div><div className="card"><div className="row"><select className="input" value={days} onChange={event => setDays(Number(event.target.value))}><option value={7}>Next 7 days</option><option value={14}>Next 14 days</option><option value={30}>Next 30 days</option></select><button className="btn" onClick={create} disabled={busy}><Sparkles size={16} /> {busy ? "Planning..." : "Create plan"}</button></div></div>{error && <p style={{ color: "var(--danger)" }}>{error}</p>}<div className="list" style={{ marginTop: 18 }}>{plan.tasks?.map((task: any) => <div className="item" key={task.day}><div className="item-name"><CalendarDays size={20} className="file-icon" /><div><b>Day {task.day}: {task.topic}</b><div className="muted" style={{ marginTop: 4 }}>{task.minutes} minutes · {task.activities.join(" · ")}</div></div></div></div>)}{!plan.tasks?.length && <div className="card empty-state">Create a plan to organize your next study sessions.</div>}</div></main></div></Guard>;
}