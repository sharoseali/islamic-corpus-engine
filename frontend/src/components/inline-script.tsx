"use client";

// Pre-paint inline script. Runs during HTML parsing on hard loads; on the
// client it renders as text/plain so React does not warn about <script> tags.
export function InlineScript({ html }: { html: string }) {
  return (
    <script
      type={typeof window === "undefined" ? "text/javascript" : "text/plain"}
      suppressHydrationWarning
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
