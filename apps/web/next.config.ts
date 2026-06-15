import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@memoryos/shared", "@memoryos/ui"],
};

export default nextConfig;
