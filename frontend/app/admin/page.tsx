"use client";

import { useEffect, useState } from "react";
import Guard from "../../components/Guard";
import Sidebar from "../../components/Sidebar";
import { api } from "../../lib/api";

export default function Admin() {
  const [stats, setStats] = useState<any>(null);
  const [error, setError] = useState("");
  useEffect(() => { api("/api/admin/stats").then(setStats).catch(err => setError(err.message)); }, []);
  return <Guard><div className="shell"><Sidebar /><main className="main"><div className="top"><div><p className="eyebrow">Restricted workspace</p><h1 className="title">Admin overview</h1><p className="subtitle">Platform-level health metrics. Access is enforced by the backend role.</p></div></div>{error ? <div className="card empty-state">{error}</div> : <div className="grid cards">{Object.entries(stats || {}).map(([key, value]) => <div className="card" key={key}><div className="label">{key.replaceAll("_", " ")}</div><div className="stat">{String(value)}</div></div>)}</div>}</main></div></Guard>;
}