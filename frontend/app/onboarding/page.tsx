"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
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
              <p className="eyebrow">Step 1 of 1</p>
              <h1 className="title">Shape your learning space</h1>
              <p className="subtitle">Tell ASKLY how you learn so future guidance can fit your goals. You can update these choices later from Profile.</p>
            </div>
          </div>
          <form className="card form" onSubmit={submit} style={{ maxWidth: 760 }}>
            <label>Education level<select className={fieldClass} value={educationLevel} onChange={e => setEducationLevel(e.target.value)}><option value="secondary">Secondary school</option><option value="undergraduate">Undergraduate</option><option value="postgraduate">Postgraduate</option><option value="professional">Professional</option><option value="other">Other</option></select></label>
            <label>Learning goal<input className={fieldClass} value={learningGoal} onChange={e => setLearningGoal(e.target.value)} placeholder="e.g. Prepare for my database exam" required /></label>
            <label>Preferred language<input className={fieldClass} value={preferredLanguage} onChange={e => setPreferredLanguage(e.target.value)} placeholder="English" required /></label>
            <label>Study subjects<input className={fieldClass} value={subjects} onChange={e => setSubjects(e.target.value)} placeholder="e.g. Python, Databases" required /><small className="muted">Separate subjects with commas.</small></label>
            <label>Daily study time in minutes<input className={fieldClass} type="number" min="10" max="720" value={dailyMinutes} onChange={e => setDailyMinutes(e.target.value)} required /></label>
            <label>Preferred study style<select className={fieldClass} value={studyStyle} onChange={e => setStudyStyle(e.target.value)}><option value="visual">Visual explanations</option><option value="reading">Reading and notes</option><option value="practice">Practice first</option><option value="discussion">Discussion and questions</option><option value="mixed">A mix of approaches</option></select></label>
            {error && <small style={{ color: "#ff9db1" }}>{error}</small>}
            <button className="btn" type="submit" disabled={busy}>{busy ? "Saving your setup…" : "Finish setup"}</button>
          </form>
        </main>
      </div>
    </Guard>
  );
}
