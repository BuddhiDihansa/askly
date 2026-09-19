"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, MessageCircle, FileText, BrainCircuit, TrendingUp, LogOut } from "lucide-react";

const items = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/chat", label: "AI Tutor", icon: MessageCircle },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/quiz", label: "Adaptive Quiz", icon: BrainCircuit },
  { href: "/progress", label: "Progress", icon: TrendingUp },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  function signOut() {
    localStorage.removeItem("askly_token");
    router.push("/login");
  }

  return (
    <aside className="sidebar">
      <Link href="/dashboard" className="brand-wrap">
        <span className="brand-mark">A</span>
        <span className="brand">ASK<span>LY</span></span>
      </Link>

      <div className="sidebar-section-label">Workspace</div>
      <nav className="nav">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link key={href} href={href} className={active ? "active" : ""}>
              <Icon size={18} strokeWidth={2} />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-bottom">
        <div className="sidebar-tip">
          <span className="status-dot" />
          <div>
            <b>ASKLY online</b>
            <small>Ready to learn with you</small>
          </div>
        </div>
        <button className="signout" onClick={signOut}>
          <LogOut size={17} />
          Sign out
        </button>
      </div>
    </aside>
  );
}
