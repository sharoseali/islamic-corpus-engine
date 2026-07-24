// A quiet, continuously scrolling line of the platform's defining features.
// Pure CSS marquee (duplicated track for a seamless loop); pauses on hover
// and respects reduced-motion.

export function Ticker({ items }: { items: string[] }) {
  if (!items.length) return null;
  const row = [...items, ...items];
  return (
    <div className="ticker" aria-hidden dir="ltr">
      <div className="ticker-track">
        {row.map((text, i) => (
          <span className="ticker-item" key={i}>
            <span className="ticker-sep" />
            {text}
          </span>
        ))}
      </div>
    </div>
  );
}
