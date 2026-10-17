/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // In dev, the frontend runs on :3000 and the backend on :8000 — proxy
    // /api/* so the browser only ever talks to one origin (this also keeps
    // the auth cookies same-site without any extra CORS dance). In
    // production, nginx does this same job in front of both containers.
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_INTERNAL_URL || "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
