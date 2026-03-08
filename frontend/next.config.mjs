/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: [],
  },
  experimental: {
    serverActions: {
      bodySizeLimit: '10mb',
    },
  },
  // Suppress the dev mode floating indicator (Next.js 15+)
  devIndicators: false,
  // Ensure production builds don't include dev code
  productionBrowserSourceMaps: false,
};

export default nextConfig;
