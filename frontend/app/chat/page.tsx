"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import Sidebar from "../../components/Sidebar";
import Guard from "../../components/Guard";
import { api } from "../../lib/api";

export default function Chat() {
  const [messages, setMessages] = useState<any[]>([]);
  const [text, setText] = useState("");
  const [cid, setCid] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api("/api/chat/conversations").then((x: any[]) => {
      if (x[0]) { setCid(x[0].id); setMessages(x[0].messages || []); }
    }).catch(() => {});
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, busy]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim() || busy) return;
    const q = text.trim();
    setText("");
    setMessages(m => [...m, { role: "user", content: q }]);
    setBusy(true);
    try {
      const x = await api("/api/chat", { method: "POST", body: JSON.stringify({ message: q, conversation_id: cid }) });
      setCid(x.conversation_id);
      setMessages(m => [...m, { role: "assistant", content: x.answer, citations: x.citations, web_sources: x.web_sources }]);
    } catch (e: any) {
      setMessages(m => [...m, { role: "assistant", content: `I couldn't complete that request: ${e.message}` }]);
    } finally { setBusy(false); }
  }

  function useAction(action: string) {
    setText(`${action}: `);
  }

  return (
    <Guard>
      <div className="shell">
        <Sidebar />
        <main className="main">
          <div className="top">
            <div>
              <p className="eyebrow">AI tutor</p>
              <h1 className="title">Study with ASKLY</h1>
              <p className="subtitle">Ask about your uploaded material, request an explanation, or explore a current question.</p>
            </div>
          </div>
          <div className="card chatbox">
            <div className="chat-head"><div className="row"><span className="quick-icon"><Sparkles size={17} /></span><div><b>ASKLY Tutor</b><small style={{ display: "block" }}>Context-aware learning assistant</small></div></div><span className="pill">Ready</span></div>
            <div className="chat-actions">
              {['Explain simpler', 'Step by step', 'Give an example', 'Summarize'].map(action => <button className="btn secondary" type="button" key={action} onClick={() => useAction(action)}>{action}</button>)}
            </div>
            <div className="messages">
              {messages.length === 0 && (
                <div className="empty-state">
                  <Sparkles size={28} style={{ color: "var(--accent-2)", marginBottom: 12 }} />
                  <h2 style={{ color: "var(--text)", margin: "0 0 7px" }}>What are you learning today?</h2>
                  <p style={{ maxWidth: 430, margin: "0 auto", lineHeight: 1.6 }}>Try “Explain database normalization simply” or ask about something inside your uploaded PDFs.</p>
                </div>
              )}
              {messages.map((m, i) => (
                <div key={i} className={`msg ${m.role}`}>
                  <div className="message-role">{m.role === "user" ? "You" : "ASKLY"}</div>
                  {m.content}
                  {m.citations?.map((c: any, j: number) => <div className="citation" key={j}>📄 {c.filename} · page {c.page}</div>)}
                  {m.web_sources?.map((c: any, j: number) => <div className="citation" key={j}>🌐 {c.title}</div>)}
                </div>
              ))}
              {busy && <div className="msg assistant loading"><div className="message-role">ASKLY</div>Thinking…</div>}
              <div ref={endRef} />
            </div>
            <form className="composer" onSubmit={send}>
              <input className="input" value={text} onChange={e => setText(e.target.value)} placeholder="Ask a study question…" aria-label="Study question" />
              <button className="btn" disabled={busy || !text.trim()}><Send size={16} style={{ verticalAlign: "-3px" }} /> Send</button>
            </form>
          </div>
        </main>
      </div>
    </Guard>
  );
}
