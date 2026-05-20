/**
 * Monorepo 共享 ESLint 规则（apps/web、packages/*）
 * 引号由 Prettier 统一，此处不配置 quotes
 */
export const sharedRules = {
  semi: ["error", "always"],
  "@typescript-eslint/no-unused-vars": "warn",
  "no-console": "off",
  "@typescript-eslint/no-empty-function": "off",
};
