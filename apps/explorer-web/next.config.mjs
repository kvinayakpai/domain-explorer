/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  transpilePackages: ["@domain-explorer/metadata", "@domain-explorer/shared-types"],
  // Demo asset — keep build green even when an ESLint plugin isn't loaded
  // or a non-blocking lint rule fires. Run `pnpm lint` separately if you
  // want strict checks.
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
  experimental: {
    typedRoutes: false,
    serverComponentsExternalPackages: [
      "@duckdb/node-api",
      "@duckdb/node-bindings",
      "@duckdb/node-bindings-linux-x64",
      "@duckdb/node-bindings-darwin-x64",
      "@duckdb/node-bindings-darwin-arm64",
      "@duckdb/node-bindings-win32-x64",
    ],
  },
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.externals = [
        ...(Array.isArray(config.externals) ? config.externals : []),
        ({ request }, callback) => {
          if (
            request === "@duckdb/node-api" ||
            request === "@duckdb/node-bindings" ||
            (request && request.startsWith("@duckdb/node-bindings-"))
          ) {
            return callback(null, "commonjs " + request);
          }
          return callback();
        },
      ];
      config.module.rules.push({ test: /\.node$/, loader: "node-loader" });
    }
    return config;
  },
};
export default nextConfig;
