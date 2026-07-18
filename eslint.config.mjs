import globals from "globals";
import pluginJs from "@eslint/js";
import eslintConfigPrettier from "eslint-config-prettier";

export default [
  {
    ignores: [
      "static/js/jquery*.js",
      "static/js/bootstrap*.js",
      "static/js/popper*.js",
      "static/js/swiper*.js",
      "static/js/*min.js",
      "static/date-time/",
      "node_modules/"
    ]
  },
  pluginJs.configs.recommended,
  eslintConfigPrettier,
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.jquery,
      },
      ecmaVersion: 2021,
      sourceType: "module"
    },
    rules: {
      "no-unused-vars": "warn",
      "no-console": "off",
      "no-undef": "warn"
    }
  }
];
