/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@domain-explorer/metadata", "@domain-explorer/shared-types"],
  experimental: {
    typedRoutes: true,
  },
};
export default nextConfig;
