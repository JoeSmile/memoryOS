import eslint from "@eslint/js";
import prettier from "eslint-config-prettier";
import tseslint from "typescript-eslint";
import { sharedRules } from "../../eslint.shared.mjs";

export default tseslint.config(
  { ignores: ["node_modules/**"] },
  eslint.configs.recommended,
  ...tseslint.configs.recommended,
  prettier,
  {
    rules: sharedRules,
  },
);
