import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@memoryos/shared", "@memoryos/ui"],
};

export default nextConfig;
