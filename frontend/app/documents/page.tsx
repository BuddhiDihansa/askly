"use client";

import { useEffect, useState } from "react";
import { FileText, Trash2, UploadCloud } from "lucide-react";
import Sidebar from "../../components/Sidebar";
import Guard from "../../components/Guard";
import { api } from "../../lib/api";

export default function Documents() {
  const [docs, setDocs] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function load() {
    try { setDocs(await api("/api/documents")); } catch (e: any) { setMsg(e.message); }
  }
  useEffect(() => { load(); }, []);

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setBusy(true); setMsg("Indexing your PDF…");
    try {
      const fd = new FormData(); fd.append("file", f);
      const uploaded = await api("/api/documents/upload", { method: "POST", body: fd });
      setMsg(uploaded.status === "completed" ? "Document indexed successfully." : "Document uploaded.");
      await load();
    } catch (e: any) { setMsg(e.message); }
    finally { setBusy(false); e.target.value = ""; }
  }

  async function del(id: string) {
    try { await api(`/api/documents/${id}`, { method: "DELETE" }); await load(); }
    catch (e: any) { setMsg(e.message); }
  }

  return (
    <Guard>
      <div className="shell">
        <Sidebar />
        <main className="main">
          <div className="top">
            <div><p className="eyebrow">Knowledge base</p><h1 className="title">My documents</h1><p className="subtitle">Give ASKLY the material you want to study. PDFs are processed into searchable learning context.</p></div>
          </div>
          <div className="card drop">
            <div>
              <div className="drop-icon"><UploadCloud size={25} /></div>
              <h2>Upload a PDF</h2>
              <p className="muted">Page-aware chunks and embeddings will be created automatically.</p>
              <input id="file" type="file" accept="application/pdf" hidden onChange={upload} />
              <label htmlFor="file" className="btn" style={{ display: "inline-block", marginTop: 8, cursor: "pointer" }}>{busy ? "Indexing…" : "Choose PDF"}</label>
              {msg && <div style={{ marginTop: 12, fontSize: 12 }}>{msg}</div>}
            </div>
          </div>

          <div className="section-head" style={{ marginTop: 25 }}><h2>Your library</h2><span className="pill">{docs.length} document{docs.length === 1 ? "" : "s"}</span></div>
          <div className="list">
            {docs.map(d => (
              <div className="item" key={d.id}>
                <div className="item-name"><FileText className="file-icon" size={20} /><div><b>{d.filename}</b><div className="muted" style={{ marginTop: 4, fontSize: 11 }}>{d.pages} pages · {d.chunks} chunks · {d.status || "completed"}</div>{d.topics?.length > 0 && <div className="muted" style={{ marginTop: 4, fontSize: 11 }}>Topics: {d.topics.slice(0, 4).join(", ")}</div>}{d.processing_error && <div style={{ marginTop: 4, fontSize: 11, color: "#ff9db1" }}>{d.processing_error}</div>}</div></div>
                <button className="btn danger" onClick={() => del(d.id)}><Trash2 size={15} style={{ verticalAlign: "-3px" }} /> Delete</button>
              </div>
            ))}
            {!docs.length && <div className="card empty-state">Your library is empty. Upload a PDF to give your tutor study context.</div>}
          </div>
        </main>
      </div>
    </Guard>
  );
}
