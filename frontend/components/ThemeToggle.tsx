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
    <div className="theme-toggle" role="group" aria-label="Color theme">
      <button className={!isLight ? "theme-choice active" : "theme-choice"} type="button" onClick={() => { if (isLight) toggleTheme(); }} aria-pressed={!isLight}>
        <Moon size={14} /> Dark
      </button>
      <button className={isLight ? "theme-choice active" : "theme-choice"} type="button" onClick={() => { if (!isLight) toggleTheme(); }} aria-pressed={isLight}>
        <Sun size={14} /> Light
      </button>
    </div>
  );
}