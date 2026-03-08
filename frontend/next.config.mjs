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
  // Disable Next.js dev indicator overlay in development
  // Note: Dev indicators are automatically disabled in production builds
  devIndicators: {
    buildActivity: false,
    buildActivityPosition: 'bottom-right',
  },
  // Ensure production builds don't include dev code
  productionBrowserSourceMaps: false,
};

export default nextConfig;
