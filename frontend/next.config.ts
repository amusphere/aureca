import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "*.railway.app",  // Hosting service for development
  ],
};

export default nextConfig;
