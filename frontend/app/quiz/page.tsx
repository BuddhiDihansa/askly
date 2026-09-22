"use client";

import { useState } from "react";
import { BrainCircuit, CheckCircle2, Sparkles } from "lucide-react";
import Sidebar from "../../components/Sidebar";
import Guard from "../../components/Guard";
import { api } from "../../lib/api";

export default function Quiz() {
  const [topic, setTopic] = useState("");
  const [quiz, setQuiz] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);

  async function gen() {
    if (!topic.trim() || busy) return;
    setBusy(true); setResult(null);
    try {
      setQuiz(await api("/api/quiz/generate", { method: "POST", body: JSON.stringify({ topic: topic.trim(), count: 5, difficulty: "adaptive" }) }));
      setAnswers({});
    } catch (e: any) { setResult({ error: e.message }); }
    finally { setBusy(false); }
  }

  async function submit() {
    // a quiz can only be submitted once (the server enforces this too)
    if (!quiz || (result && !result.error)) return;
    try { setResult(await api("/api/quiz/submit", { method: "POST", body: JSON.stringify({ quiz_id: quiz.quiz_id, answers }) })); }
    catch (e: any) { setResult({ error: e.message }); }
  }

  return (
    <Guard>
      <div className="shell">
        <Sidebar />
        <main className="main">
          <div className="top"><div><p className="eyebrow">Practice engine</p><h1 className="title">Adaptive quiz</h1><p className="subtitle">Choose a topic and ASKLY will generate five questions using your current mastery estimate.</p></div></div>

          <div className="card">
            <div className="row" style={{ alignItems: "stretch" }}>
              <input className="input" value={topic} onChange={e => setTopic(e.target.value)} onKeyDown={e => { if (e.key === "Enter") gen(); }} placeholder="Topic, e.g. Database Normalization" />
              <button className="btn" onClick={gen} disabled={busy || !topic.trim()}><Sparkles size={16} style={{ verticalAlign: "-3px" }} /> {busy ? "Generating…" : "Generate quiz"}</button>
            </div>
          </div>

          {quiz && (
            <div className="card" style={{ marginTop: 18 }}>
              <div className="section-head">
                <div><h2>{quiz.topic}</h2><div className="quiz-meta" style={{ marginTop: 8 }}><span className="pill">{quiz.difficulty}</span><span className="pill">Mastery {Math.round(quiz.mastery * 100)}%</span><span className="pill">5 questions</span></div></div>
                <BrainCircuit size={25} style={{ color: "var(--accent-2)" }} />
              </div>
              {quiz.questions.map((q: any, i: number) => (
                <div className="quizq" key={i}>
                  <b>{i + 1}. {q.question}</b>
                  {q.options.map((o: string, j: number) => (
                    <button className={`option ${answers[i] === j ? "selected" : ""}`} key={j} onClick={() => setAnswers(a => ({ ...a, [i]: j }))}>
                      {String.fromCharCode(65 + j)}. {o}
                    </button>
                  ))}
                </div>
              ))}
              <button className="btn" onClick={submit} disabled={Object.keys(answers).length !== quiz.questions.length || (!!result && !result.error)}><CheckCircle2 size={16} style={{ verticalAlign: "-3px" }} /> Submit & update mastery</button>

              {result && !result.error && (
                <div className="card" style={{ marginTop: 18, background: "rgba(67,217,197,.06)", borderColor: "rgba(67,217,197,.18)" }}>
                  <p className="eyebrow">Quiz complete</p>
                  <h2>Score: {result.correct}/{result.total}</h2>
                  <p className="muted">Your new {result.topic} mastery is <b style={{ color: "var(--text)" }}>{Math.round(result.new_mastery * 100)}%</b>.</p>
                </div>
              )}
              {result?.error && <p style={{ color: "#ff9db1" }}>{result.error}</p>}
            </div>
          )}
        </main>
      </div>
    </Guard>
  );
}
