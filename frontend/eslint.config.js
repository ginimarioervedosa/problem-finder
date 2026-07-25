// The frontend quality gates: TS strict linting, file ceilings, complexity,
// and the routes -> features -> shared layering, mirrored from the backend's
// import-linter contract.
import js from "@eslint/js";
import boundaries from "eslint-plugin-boundaries";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    ignores: [
      "dist",
      "node_modules",
      "src/routeTree.gen.ts",
      "src/api/schema.d.ts",
      "src/components/ui/**",
      "vite.config.ts",
      "eslint.config.js",
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  {
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
      globals: globals.browser,
    },
    plugins: { boundaries },
    settings: {
      "boundaries/elements": [
        { type: "app", pattern: ["src/main.tsx"], mode: "full" },
        { type: "routes", pattern: "src/routes/**" },
        { type: "features", pattern: "src/features/*/**", capture: ["feature"] },
        { type: "shared", pattern: ["src/components/**", "src/api/**", "src/lib/**"] },
      ],
    },
    rules: {
      "max-lines": ["error", { max: 250, skipBlankLines: false, skipComments: false }],
      complexity: ["error", 10],
      "@typescript-eslint/no-explicit-any": "error",
      "boundaries/dependencies": [
        "error",
        {
          default: "disallow",
          policies: [
            {
              from: { type: "app" },
              allow: [{ type: "routes" }, { type: "features" }, { type: "shared" }],
            },
            { from: { type: "routes" }, allow: [{ type: "features" }, { type: "shared" }] },
            {
              from: { type: "features" },
              allow: [{ type: "features", feature: "{{from.feature}}" }, { type: "shared" }],
            },
            { from: { type: "shared" }, allow: [{ type: "shared" }] },
          ],
        },
      ],
    },
  },
  {
    files: ["tests/**"],
    rules: { "boundaries/dependencies": "off" },
  },
);
