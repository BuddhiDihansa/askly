"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Orb3D from "../../components/Orb3D";
import { api, saveToken } from "../../lib/api";

export default function Login() {
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
      const x = await api("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      saveToken(x.token);
      r.push(x.user?.onboarding_completed ? "/dashboard" : "/onboarding");
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth">
      <div className="auth-layout">
        <section className="authbox">
          <div className="brand-wrap" style={{ padding: 0 }}>
            <span className="brand-mark">A</span><span className="brand">ASK<span>LY</span></span>
          </div>
          <h1>Welcome back</h1>
          <p className="muted">Continue your personalized learning workspace.</p>
          <form className="form" onSubmit={go}>
            <input className="input" placeholder="Email address" type="email" value={email} onChange={e => setEmail(e.target.value)} required />
            <input className="input" placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} required />
            {err && <small style={{ color: "#ff9db1" }}>{err}</small>}
            <button className="btn" disabled={loading}>{loading ? "Signing in…" : "Sign in"}</button>
          </form>
          <p className="muted" style={{ marginTop: 20, fontSize: 13 }}>New to ASKLY? <Link href="/register" style={{ color: "var(--accent-2)" }}>Create an account</Link></p>
        </section>
        <section className="auth-visual">
          <Orb3D />
          <div className="auth-visual-copy">
            <h2>One workspace. Your whole learning loop.</h2>
            <p>Context from your documents, focused conversations and adaptive practice—connected in one interface.</p>
          </div>
        </section>
      </div>
    </main>
  );
}
