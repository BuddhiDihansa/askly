"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, BookOpen, BrainCircuit, MessageCircle, Sparkles } from "lucide-react";
import Sidebar from "../../components/Sidebar";
import Guard from "../../components/Guard";
import { api } from "../../lib/api";

const fieldClass = "input";

export default function Onboarding() {
  const router = useRouter();
  const [educationLevel, setEducationLevel] = useState("undergraduate");
  const [learningGoal, setLearningGoal] = useState("");
  const [preferredLanguage, setPreferredLanguage] = useState("English");
  const [subjects, setSubjects] = useState("");
  const [dailyMinutes, setDailyMinutes] = useState("30");
  const [studyStyle, setStudyStyle] = useState("mixed");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api("/api/profile/onboarding", {
        method: "POST",
        body: JSON.stringify({
          education_level: educationLevel,
          learning_goal: learningGoal,
          preferred_language: preferredLanguage,
          study_subjects: subjects.split(",").map(subject => subject.trim()).filter(Boolean),
          daily_study_minutes: Number(dailyMinutes),
          study_style: studyStyle,
        }),
      });
      router.replace("/dashboard");
    } catch (err: any) {
      setError(err.message || "We could not save your learning preferences.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Guard>
      <div className="shell">
        <Sidebar />
        <main className="main">
          <div className="top">
            <div>
              <p className="eyebrow">Welcome to your learning space</p>
              <h1 className="title">Let’s make studying feel lighter.</h1>
              <p className="subtitle">A few details help ASKLY meet you at the right level. You can change them any time from Profile.</p>
            </div>
          </div>
          <div className="onboarding-grid">
            <section className="card welcome-guide">
              <div className="welcome-mark"><Sparkles size={21} /></div>
              <h2>Your simple study loop</h2>
              <p className="muted">Use ASKLY in four calm steps. No need to set everything up at once.</p>
              <div className="guide-steps">
                <div className="guide-step"><span><BookOpen size={17} /></span><div><b>Bring your material</b><small>Upload a PDF and keep your course context in one place.</small></div></div>
                <div className="guide-step"><span><MessageCircle size={17} /></span><div><b>Ask without pressure</b><small>Ask for a simpler explanation, an example, or a step-by-step answer.</small></div></div>
                <div className="guide-step"><span><BrainCircuit size={17} /></span><div><b>Practice what matters</b><small>Use quizzes and flashcards to turn understanding into memory.</small></div></div>
                <div className="guide-step"><span><ArrowRight size={17} /></span><div><b>Notice your progress</b><small>Return to your dashboard when you want a clear next step.</small></div></div>
              </div>
            </section>
            <form className="card form onboarding-form" onSubmit={submit}>
              <div><p className="eyebrow">Step 1 of 1</p><h2>Personalize ASKLY</h2></div>
              <label>Education level<select className={fieldClass} value={educationLevel} onChange={e => setEducationLevel(e.target.value)}><option value="secondary">Secondary school</option><option value="undergraduate">Undergraduate</option><option value="postgraduate">Postgraduate</option><option value="professional">Professional</option><option value="other">Other</option></select></label>
              <label>Learning goal<input className={fieldClass} value={learningGoal} onChange={e => setLearningGoal(e.target.value)} placeholder="e.g. Prepare for my database exam" required /></label>
              <label>Preferred language<input className={fieldClass} value={preferredLanguage} onChange={e => setPreferredLanguage(e.target.value)} placeholder="English" required /></label>
              <label>Study subjects<input className={fieldClass} value={subjects} onChange={e => setSubjects(e.target.value)} placeholder="e.g. Python, Databases" required /><small className="muted">Separate subjects with commas.</small></label>
              <label>Daily study time in minutes<input className={fieldClass} type="number" min="10" max="720" value={dailyMinutes} onChange={e => setDailyMinutes(e.target.value)} required /></label>
              <label>Preferred study style<select className={fieldClass} value={studyStyle} onChange={e => setStudyStyle(e.target.value)}><option value="visual">Visual explanations</option><option value="reading">Reading and notes</option><option value="practice">Practice first</option><option value="discussion">Discussion and questions</option><option value="mixed">A mix of approaches</option></select></label>
              {error && <small style={{ color: "#ff9db1" }}>{error}</small>}
              <button className="btn" type="submit" disabled={busy}>{busy ? "Saving your setup…" : "Enter my workspace"} <ArrowRight size={16} style={{ verticalAlign: "-3px" }} /></button>
            </form>
          </div>
        </main>
      </div>
    </Guard>
  );
}
