"use client";

export default function Orb3D({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`orb-stage ${compact ? "orb-stage-compact" : ""}`} role="img" aria-label="Animated ASKLY learning orb">
      <div className="orb-glow" />
      <div className="orb">
        <div className="orb-core" />
        <span className="orb-ring ring-a" />
        <span className="orb-ring ring-b" />
        <span className="orb-ring ring-c" />
        <span className="orb-dot dot-a" />
        <span className="orb-dot dot-b" />
        <span className="orb-dot dot-c" />
      </div>
      <div className="orb-shadow" />
    </div>
  );
}
