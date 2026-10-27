import { ElaajLoader } from "@/components/elaaj-loader";

// Shown instantly while a page's data streams in on navigation.
export default function Loading() {
  return (
    <div style={{ minHeight: "55vh", display: "grid", placeItems: "center" }}>
      <ElaajLoader />
    </div>
  );
}
