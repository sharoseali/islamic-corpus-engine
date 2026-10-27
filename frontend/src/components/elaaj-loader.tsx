"use client";

import { useI18n } from "./providers";

// Branded loading mark: the ع seal inside a slowly turning girih star,
// with a gold ring tracing around it. Colors come from theme tokens, so it
// reads the same in light and dark themes.
export function ElaajLoader({
  label,
  size = "md",
}: {
  label?: string;
  size?: "sm" | "md";
}) {
  const { dict } = useI18n();
  const text = label ?? dict.common.loading;

  return (
    <div className={`elaaj-loader elaaj-loader--${size}`} role="status" aria-live="polite">
      <div className="elaaj-loader__mark" aria-hidden>
        <svg viewBox="0 0 120 120" className="elaaj-loader__svg">
          {/* faint track + tracing ring */}
          <circle cx="60" cy="60" r="54" className="elaaj-loader__track" />
          <circle cx="60" cy="60" r="54" className="elaaj-loader__ring" pathLength="100" />
          {/* eight-point girih star (two squares), turning slowly */}
          <g className="elaaj-loader__star">
            <rect x="27" y="27" width="66" height="66" rx="2" />
            <rect x="27" y="27" width="66" height="66" rx="2" transform="rotate(45 60 60)" />
          </g>
          {/* inner ring, counter-turning */}
          <g className="elaaj-loader__inner">
            <circle cx="60" cy="60" r="30" />
            {[0, 45, 90, 135, 180, 225, 270, 315].map((a) => (
              <circle key={a} cx="60" cy="30" r="1.6" transform={`rotate(${a} 60 60)`} className="elaaj-loader__dot" />
            ))}
          </g>
        </svg>
        <span className="elaaj-loader__seal">ع</span>
      </div>
      {size === "md" && <div className="elaaj-loader__name">علاج بالدعاء</div>}
      <div className="elaaj-loader__label">
        {text.replace(/[….]+$/u, "")}
        <span className="elaaj-loader__dots">
          <span>.</span>
          <span>.</span>
          <span>.</span>
        </span>
      </div>
    </div>
  );
}
