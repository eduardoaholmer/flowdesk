export default {
  "*.{ts,tsx}": ["eslint --fix", "prettier --write", () => "tsc -b --noEmit"],
  "*.{css,md,json}": ["prettier --write"],
};
