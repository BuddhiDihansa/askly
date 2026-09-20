"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

type Theme = "light" | "dark";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    const saved = window.localStorage.getItem("askly_theme") as Theme | null;
    const next = saved === "light" || saved === "dark" ? saved : "dark";
    setTheme(next);
    document.documentElement.dataset.theme = next;
  }, []);

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    window.localStorage.setItem("askly_theme", next);
    document.documentElement.dataset.theme = next;
  }

  const isLight = theme === "light";
  return (
    <button
      className="theme-toggle"
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${isLight ? "dark" : "light"} mode`}
      title={`Switch to ${isLight ? "dark" : "light"} mode`}
    >
      {isLight ? <Moon size={16} /> : <Sun size={16} />}
    </button>
  );
}