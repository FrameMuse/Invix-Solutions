import type { NextConfig } from "next"

const isPages = process.env.GITHUB_PAGES === "true"

const nextConfig: NextConfig = {
  output: isPages ? "export" : "standalone",
  basePath: isPages ? "/Invix-Solutions" : undefined,
  images: {
    unoptimized: isPages
  },
  trailingSlash: isPages
}

export default nextConfig
