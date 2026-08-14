import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    const backendOrigin = process.env.API_INTERNAL_BASE_URL ?? "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: `${backendOrigin}/api/:path*` }];
  },
};

export default nextConfig;
