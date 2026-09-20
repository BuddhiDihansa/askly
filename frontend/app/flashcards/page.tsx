"use client";

import { useEffect, useState } from "react";
import { Layers3, RotateCcw, Sparkles } from "lucide-react";
import Guard from "../../components/Guard";
import Sidebar from "../../components/Sidebar";
import { api } from "../../lib/api";

type Card = { id: string; front: string; back: string; topic: string; source?: { filename?: string; page?: number }; repetitions: number };

export default function Flashcards() {
  const [topic, setTopic] = useState("");
  const [cards, setCards] = useState<Card[]>([]);
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { api("/api/flashcards?due_only=true").then(setCards).catch(() => {}); }, []);

  async function generate() {
    if (!topic.trim() || busy) return;
    setBusy(true); setError("");
    try { const result = await api("/api/flashcards/generate", { method: "POST", body: JSON.stringify({ topic: topic.trim(), count: 5 }) }); setCards(result.cards); setIndex(0); setRevealed(false); }
    catch (err: any) { setError(err.message || "Could not create flashcards."); }
    finally { setBusy(false); }
  }

  async function review(rating: "again" | "hard" | "good" | "easy") {
    const card = cards[index];
    if (!card) return;
    try { await api(`/api/flashcards/${card.id}/review`, { method: "POST", body: JSON.stringify({ rating }) }); setIndex(value => value + 1); setRevealed(false); }
    catch (err: any) { setError(err.message || "Could not save review."); }
  }

  const card = cards[index];
  return <Guard><div className="shell"><Sidebar /><main className="main">
    <div className="top"><div><p className="eyebrow">Spaced repetition</p><h1 className="title">Flashcards</h1><p className="subtitle">Turn your uploaded material into small, repeatable review sessions.</p></div></div>
    <div className="card"><div className="row"><input className="input" value={topic} onChange={event => setTopic(event.target.value)} onKeyDown={event => { if (event.key === "Enter") generate(); }} placeholder="Topic from your documents" /><button className="btn" onClick={generate} disabled={busy || !topic.trim()}><Sparkles size={16} /> {busy ? "Creating..." : "Create cards"}</button></div></div>
    {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
    {card ? <div className="card flashcard-stage"><div className="section-head"><span className="pill">Card {index + 1} of {cards.length}</span><Layers3 size={23} style={{ color: "var(--accent-2)" }} /></div><button className="flashcard" onClick={() => setRevealed(value => !value)}><span className="eyebrow">{revealed ? "Answer" : "Prompt"}</span><strong>{revealed ? card.back : card.front}</strong>{card.source?.filename && <small>{card.source.filename} · page {card.source.page}</small>}</button>{revealed && <div className="hero-actions"><button className="btn danger" onClick={() => review("again")}>Again</button><button className="btn secondary" onClick={() => review("hard")}>Hard</button><button className="btn secondary" onClick={() => review("good")}>Good</button><button className="btn" onClick={() => review("easy")}>Easy</button></div>}</div> : <div className="card empty-state"><RotateCcw size={28} style={{ color: "var(--accent-2)" }} /><p>{cards.length ? "Review complete for now." : "Create cards from a topic in your uploaded documents."}</p></div>}
  </main></div></Guard>;
}