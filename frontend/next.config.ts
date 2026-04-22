import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  // Next.js gzip buffers SSE streams proxied via rewrites until a compression
  // block fills, delaying events by tens of seconds. Disable it; the backend
  // already streams with the correct text/event-stream headers.
  compress: false,
  async rewrites() {
    return [
      { source: "/validate", destination: `${backendUrl}/validate` },
      { source: "/research", destination: `${backendUrl}/research` },
      { source: "/health", destination: `${backendUrl}/health` },
    ];
  },
};

export default nextConfig;
