/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  transpilePackages: ["@domain-explorer/metadata", "@domain-explorer/shared-types"],
  experimental: {
    typedRoutes: false,
    serverComponentsExternalPackages: [
      "@duckdb/node-api",
      "@duckdb/node-bindings",
      "@duckdb/node-bindings-linux-x64",
      "@duckdb/node-bindings-darwin-x64",
      "@duckdb/node-bindings-darwin-arm64",
      "@duckdb/node-bindings-win32-x64",
      "pg",
      "pg-native",
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
            (request && request.startsWith("@duckdb/node-bindings-")) ||
            request === "pg" ||
            request === "pg-native"
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
