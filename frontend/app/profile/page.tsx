"use client";

import { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Guard from "../../components/Guard";
import { api } from "../../lib/api";

export default function Profile() {
  const [profile, setProfile] = useState<any>(null);
  const [subjects, setSubjects] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api("/api/profile")
      .then((data) => {
        setProfile(data);
        setSubjects((data.study_subjects || []).join(", "));
      })
      .catch((err) => setError(err.message));
  }, []);

  function change(field: string, value: string | number) {
    setProfile((current: any) => ({ ...current, [field]: value }));
  }

  async function save(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    setError("");
    try {
      const updated = await api("/api/profile", {
        method: "PUT",
        body: JSON.stringify({
          name: profile.name,
          education_level: profile.education_level,
          learning_goal: profile.learning_goal,
          preferred_language: profile.preferred_language,
          study_subjects: subjects.split(",").map(subject => subject.trim()).filter(Boolean),
          daily_study_minutes: Number(profile.daily_study_minutes),
          study_style: profile.study_style,
        }),
      });
      setProfile(updated);
      setSubjects((updated.study_subjects || []).join(", "));
      setMessage("Profile saved.");
    } catch (err: any) {
      setError(err.message || "We could not save your profile.");
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
              <p className="eyebrow">Your settings</p>
              <h1 className="title">Profile</h1>
              <p className="subtitle">Keep your learning preferences current so ASKLY can meet you where you are.</p>
            </div>
          </div>
          {profile && <form className="card form" onSubmit={save} style={{ maxWidth: 760 }}>
            <label>Name<input className="input" value={profile.name || ""} onChange={e => change("name", e.target.value)} required /></label>
            <label>Email<input className="input" value={profile.email || ""} disabled /></label>
            <label>Education level<select className="input" value={profile.education_level || "undergraduate"} onChange={e => change("education_level", e.target.value)}><option value="secondary">Secondary school</option><option value="undergraduate">Undergraduate</option><option value="postgraduate">Postgraduate</option><option value="professional">Professional</option><option value="other">Other</option></select></label>
            <label>Learning goal<input className="input" value={profile.learning_goal || ""} onChange={e => change("learning_goal", e.target.value)} required /></label>
            <label>Preferred language<input className="input" value={profile.preferred_language || "English"} onChange={e => change("preferred_language", e.target.value)} required /></label>
            <label>Study subjects<input className="input" value={subjects} onChange={e => setSubjects(e.target.value)} required /></label>
            <label>Daily study time in minutes<input className="input" type="number" min="10" max="720" value={profile.daily_study_minutes || ""} onChange={e => change("daily_study_minutes", e.target.value)} required /></label>
            <label>Preferred study style<select className="input" value={profile.study_style || "mixed"} onChange={e => change("study_style", e.target.value)}><option value="visual">Visual explanations</option><option value="reading">Reading and notes</option><option value="practice">Practice first</option><option value="discussion">Discussion and questions</option><option value="mixed">A mix of approaches</option></select></label>
            <p className="muted" style={{ margin: 0, fontSize: 12 }}>Onboarding status: {profile.onboarding_completed ? "Complete" : "Not complete"}</p>
            {message && <small style={{ color: "var(--good)" }}>{message}</small>}
            {error && <small style={{ color: "#ff9db1" }}>{error}</small>}
            <button className="btn" type="submit" disabled={busy}>{busy ? "Saving…" : "Save profile"}</button>
          </form>}
        </main>
      </div>
    </Guard>
  );
}
