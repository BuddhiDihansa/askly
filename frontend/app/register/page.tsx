"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Orb3D from "../../components/Orb3D";
import { api, saveToken } from "../../lib/api";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const r = useRouter();

  async function go(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErr("");
    try {
      const x = await api("/api/auth/register", { method: "POST", body: JSON.stringify({ name, email, password }) });
      saveToken(x.token);
      r.push("/dashboard");
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth">
      <div className="auth-layout">
        <section className="auth-visual">
          <Orb3D />
          <div className="auth-visual-copy">
            <h2>Build knowledge that sticks.</h2>
            <p>ASKLY adapts practice to your learning progress while keeping your study context close at hand.</p>
          </div>
        </section>
        <section className="authbox">
          <div className="brand-wrap" style={{ padding: 0 }}>
            <span className="brand-mark">A</span><span className="brand">ASK<span>LY</span></span>
          </div>
          <h1>Create your workspace</h1>
          <p className="muted">Set up your personalized AI study space.</p>
          <form className="form" onSubmit={go}>
            <input className="input" placeholder="Full name" value={name} onChange={e => setName(e.target.value)} required />
            <input className="input" placeholder="Email address" type="email" value={email} onChange={e => setEmail(e.target.value)} required />
            <input className="input" placeholder="Password (6+ characters)" type="password" value={password} onChange={e => setPassword(e.target.value)} minLength={6} required />
            {err && <small style={{ color: "#ff9db1" }}>{err}</small>}
            <button className="btn" disabled={loading}>{loading ? "Creating…" : "Create account"}</button>
          </form>
          <p className="muted" style={{ marginTop: 20, fontSize: 13 }}>Already registered? <Link href="/login" style={{ color: "var(--accent-2)" }}>Sign in</Link></p>
        </section>
      </div>
    </main>
  );
}
