"use client";

import { useEffect, useState } from "react";
import { Bell, Check } from "lucide-react";
import Guard from "../../components/Guard";
import Sidebar from "../../components/Sidebar";
import { api } from "../../lib/api";

export default function Notifications() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => { api("/api/notifications").then(setItems).catch(() => {}); }, []);
  async function read(id: string) { await api(`/api/notifications/${id}/read`, { method: "POST" }); setItems(value => value.map(item => item.id === id ? { ...item, read: true } : item)); }
  return <Guard><div className="shell"><Sidebar /><main className="main"><div className="top"><div><p className="eyebrow">Stay on track</p><h1 className="title">Notifications</h1><p className="subtitle">Your review reminders and learning recommendations.</p></div></div><div className="list">{items.map(item => <div className={`item ${item.read ? "muted" : ""}`} key={item.id}><div className="item-name"><Bell size={19} /><div><b>{item.title}</b><div style={{ marginTop: 4 }}>{item.message}</div></div></div>{!item.read && <button className="btn secondary" onClick={() => read(item.id)} aria-label="Mark notification read"><Check size={16} /></button>}</div>)}{!items.length && <div className="card empty-state">You are all caught up.</div>}</div></main></div></Guard>;
}