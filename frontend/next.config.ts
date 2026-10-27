import path from "node:path";
import type { NextConfig } from "next";

const BACKEND_API = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8400/api/v1";

const nextConfig: NextConfig = {
  // Self-contained production build for the Docker image (frontend/Dockerfile
  // sets NEXT_STANDALONE and runs .next/standalone/server.js). Local
  // `npm run build && npm run start` keeps the regular output.
  output: process.env.NEXT_STANDALONE ? "standalone" : undefined,
  // Pin the workspace root: a stray lockfile in a parent directory
  // otherwise makes Turbopack infer the wrong root.
  turbopack: {
    root: path.resolve(__dirname),
  },
  // Allow opening the dev server from other devices on the LAN. Without
  // this, the HMR socket is refused and the page never hydrates.
  allowedDevOrigins: ["192.168.*.*", "127.0.0.1"],
  // Browser code calls /api/v1 on this origin; forward it to the backend.
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${BACKEND_API}/:path*` }];
  },
};

export default nextConfig;
