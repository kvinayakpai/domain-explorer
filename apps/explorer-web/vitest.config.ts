import { defineConfig } from "vitest/config";
import { resolve } from "node:path";

export default defineConfig({
  resolve: {
    alias: {
      "@": resolve(__dirname),
      "@/lib/kg": resolve(__dirname, "lib/kg.ts"),
      "@domain-explorer/metadata": resolve(__dirname, "..", "..", "packages", "metadata", "src", "index.ts"),
      "@domain-explorer/metadata/schema": resolve(__dirname, "..", "..", "packages", "metadata", "src", "schema.ts"),
    },
  },
  test: {
    environment: "node",
    include: ["__tests__/**/*.test.ts"],
    server: {
      deps: {
        // The lib/kg.ts file imports "server-only" — vitest needs to resolve it.
        inline: ["server-only"],
      },
    },
  },
});
