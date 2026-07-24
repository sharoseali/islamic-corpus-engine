import type { CSSProperties, ReactNode } from "react";

export function Container({
  children,
  style,
  narrow,
  className,
}: {
  children: ReactNode;
  style?: CSSProperties;
  narrow?: boolean;
  className?: string;
}) {
  return (
    <div
      className={className}
      style={{
        maxWidth: narrow ? 820 : 1140,
        margin: "0 auto",
        padding: "0 20px",
        ...style,
      }}
    >
      {children}
    </div>
  );
}

export function PageTitle({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <div style={{ margin: "40px 0 28px" }}>
      <h1 style={{ fontSize: 30, fontWeight: 700, margin: 0, letterSpacing: "-0.02em" }}>
        {title}
      </h1>
      {subtitle && (
        <p style={{ color: "var(--text-muted)", margin: "8px 0 0", fontSize: 16 }}>
          {subtitle}
        </p>
      )}
    </div>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "accent" | "gold";
}) {
  const tones: Record<string, CSSProperties> = {
    neutral: { background: "var(--surface-2)", color: "var(--text-muted)" },
    accent: { background: "var(--accent-soft)", color: "var(--accent)" },
    gold: { background: "var(--gold-soft)", color: "var(--gold)" },
  };
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        padding: "3px 10px",
        borderRadius: 999,
        fontSize: 12.5,
        fontWeight: 600,
        ...tones[tone],
      }}
    >
      {children}
    </span>
  );
}
