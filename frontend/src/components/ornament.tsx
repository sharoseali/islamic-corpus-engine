// Authentic Islamic geometry (girih): an 8-point star-and-diamond lattice.
// Used as a fine gold ornament band and as a faint background field.
// Pure SVG, theme-aware via currentColor / CSS variables.

function GirihDefs({ id }: { id: string }) {
  return (
    <defs>
      <pattern id={id} width="40" height="40" patternUnits="userSpaceOnUse">
        <g fill="none" stroke="currentColor" strokeWidth="1">
          {/* diamond touches tile edges so the lattice is continuous */}
          <polygon points="20,0 40,20 20,40 0,20" />
          {/* square overlaps the diamond to form the 8-point star */}
          <polygon points="7,7 33,7 33,33 7,33" />
        </g>
        <circle cx="20" cy="20" r="1.3" fill="currentColor" />
      </pattern>
    </defs>
  );
}

/** A slim horizontal ornament band (a hairline gold divider), tiled full-width. */
export function GirihBand({
  height = 34,
  opacity = 0.6,
}: {
  height?: number;
  opacity?: number;
}) {
  return (
    <svg
      aria-hidden
      width="100%"
      height={height}
      style={{ display: "block", color: "var(--gold)", opacity }}
    >
      <GirihDefs id="girih-band" />
      <rect width="100%" height={height} fill="url(#girih-band)" />
    </svg>
  );
}

/** Mihrab (prayer-niche) arch that stretches to frame the hero content.
 *  Uses preserveAspectRatio="none" so the columns land at the frame's edges
 *  regardless of its height; non-scaling strokes keep the line weight even. */
export function MihrabArch() {
  return (
    <svg
      aria-hidden
      className="hero-mihrab"
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      fill="none"
    >
      <g stroke="currentColor" fill="none" strokeLinejoin="round" vectorEffect="non-scaling-stroke">
        {/* pishtaq: the rectangular portal frame around the door */}
        <path d="M1 100 L1 3 L99 3 L99 100" strokeWidth="2.2" />
        {/* the door: a pointed arch recessed within the portal */}
        <path d="M10 100 L10 46 Q10 12 50 8 Q90 12 90 46 L90 100" strokeWidth="2.4" />
        {/* inner echo of the arch */}
        <path d="M18 100 L18 49 Q18 20 50 16 Q82 20 82 49 L82 100" strokeWidth="1.3" opacity="0.5" />
        {/* column capitals at the springing line */}
        <path d="M4 46 L16 46 M84 46 L96 46" strokeWidth="1.7" />
      </g>
    </svg>
  );
}

/** A slim flanking arch/pillar, placed at the hero edges to form a facade
 *  around the central mihrab. Fades into the wall at its base (CSS mask). */
export function SideArch() {
  return (
    <svg
      aria-hidden
      className="hero-side-arch"
      viewBox="0 0 120 400"
      preserveAspectRatio="xMidYMax meet"
      fill="none"
    >
      <g stroke="currentColor" fill="none" strokeLinejoin="round" vectorEffect="non-scaling-stroke">
        <path d="M22 400 L22 150 Q22 72 60 42 Q98 72 98 150 L98 400" strokeWidth="2" />
        <path d="M33 400 L33 158 Q33 96 60 70 Q87 96 87 158 L87 400" strokeWidth="1.3" opacity="0.55" />
      </g>
    </svg>
  );
}

/** A faint full-bleed geometric field, for subtle background texture.
 *  Opacity is theme-aware via CSS (className). A unique patternId per use
 *  avoids duplicate SVG ids when several fields render on one page. */
export function GirihField({
  className = "hero-girih",
  patternId = "girih-field",
}: {
  className?: string;
  patternId?: string;
}) {
  return (
    <svg
      aria-hidden
      className={className}
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid slice"
      style={{
        position: "absolute",
        inset: 0,
        color: "var(--gold)",
        pointerEvents: "none",
      }}
    >
      <GirihDefs id={patternId} />
      <rect width="100%" height="100%" fill={`url(#${patternId})`} />
    </svg>
  );
}

const MARK_STYLE = { display: "block" as const, color: "var(--gold)" };

/** Open book - the Quran. */
export function BookMark({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" aria-hidden style={MARK_STYLE}>
      <g stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round">
        <path d="M20 11 C16 8 9 8 5 10 L5 31 C9 29 16 29 20 32" />
        <path d="M20 11 C24 8 31 8 35 10 L35 31 C31 29 24 29 20 32" />
        <line x1="20" y1="11" x2="20" y2="32" />
      </g>
    </svg>
  );
}

/** Interlocking links - the isnad (chain of narration) for Hadith. */
export function ChainMark({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" aria-hidden style={MARK_STYLE}>
      <g stroke="currentColor" strokeWidth="1.6">
        <rect x="5" y="14.5" width="20" height="11" rx="5.5" />
        <rect x="15" y="14.5" width="20" height="11" rx="5.5" />
      </g>
    </svg>
  );
}

/** Layered, annotated pages - Tafsir (commentary). */
export function PagesMark({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" aria-hidden style={MARK_STYLE}>
      <g stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round">
        <rect x="13" y="7" width="21" height="27" rx="2" />
        <rect x="6" y="11" width="21" height="27" rx="2" fill="var(--surface)" />
        <line x1="11" y1="19" x2="22" y2="19" strokeWidth="1.2" />
        <line x1="11" y1="24" x2="22" y2="24" strokeWidth="1.2" />
        <line x1="11" y1="29" x2="18" y2="29" strokeWidth="1.2" />
      </g>
    </svg>
  );
}

/** A small centered rosette mark, used above the title like an illumination. */
export function StarMark({ size = 46 }: { size?: number }) {
  return (
    <svg
      aria-hidden
      width={size}
      height={size}
      viewBox="0 0 48 48"
      style={{ display: "block", color: "var(--gold)" }}
    >
      <g fill="none" stroke="currentColor" strokeWidth="1.4">
        <polygon points="24,3 45,24 24,45 3,24" />
        <polygon points="9,9 39,9 39,39 9,39" />
        <circle cx="24" cy="24" r="8" />
      </g>
      <circle cx="24" cy="24" r="2.4" fill="currentColor" />
    </svg>
  );
}
