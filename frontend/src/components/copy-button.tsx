"use client";

import { useState } from "react";

type Font = "arabic" | "urdu" | "plain";

const FONT_STACK: Record<Font, string> = {
  arabic: "'Amiri','Scheherazade New','Times New Roman',serif",
  urdu: "'Noto Nastaliq Urdu','Amiri',serif",
  plain: "inherit",
};

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

export function CopyButton({
  text,
  reference,
  font = "plain",
  dir = "ltr",
  title = "Copy",
}: {
  text: string;
  reference?: string;
  font?: Font;
  dir?: "rtl" | "ltr";
  title?: string;
}) {
  const [copied, setCopied] = useState(false);

  const doCopy = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const plain = reference ? `${text}\n\n${reference}` : text;
    const html =
      `<div dir="${dir}" style="font-family:${FONT_STACK[font]};font-size:${
        font === "plain" ? "1em" : "1.4em"
      };line-height:2">` +
      escapeHtml(text).replace(/\n/g, "<br>") +
      (reference
        ? `<br><br><span style="font-family:sans-serif;color:#8a8a8a;font-size:0.8em">${escapeHtml(
            reference,
          )}</span>`
        : "") +
      `</div>`;
    try {
      if (
        typeof ClipboardItem !== "undefined" &&
        navigator.clipboard?.write
      ) {
        await navigator.clipboard.write([
          new ClipboardItem({
            "text/plain": new Blob([plain], { type: "text/plain" }),
            "text/html": new Blob([html], { type: "text/html" }),
          }),
        ]);
      } else {
        await navigator.clipboard.writeText(plain);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // no-op if clipboard is unavailable
    }
  };

  return (
    <button
      onClick={doCopy}
      title={title}
      aria-label={title}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        border: "1px solid var(--border)",
        background: copied ? "var(--accent-soft)" : "var(--surface)",
        color: copied ? "var(--accent)" : "var(--text-muted)",
        borderRadius: 8,
        padding: "4px 9px",
        fontSize: 12,
        fontWeight: 600,
        cursor: "pointer",
        fontFamily: "inherit",
        transition: "all 0.15s",
      }}
    >
      <span aria-hidden style={{ fontSize: 13 }}>
        {copied ? "✓" : "⧉"}
      </span>
    </button>
  );
}
