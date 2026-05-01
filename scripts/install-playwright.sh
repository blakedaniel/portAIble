#!/usr/bin/env bash
# install-playwright.sh — one-shot installer for Phase 2.5 Playwright e2e.
#
# What this does (in order):
#   1. Installs `@playwright/test` as a frontend devDependency (npm).
#   2. Downloads the Chromium browser into the per-user Playwright cache
#      (~/.cache/ms-playwright). No sudo needed for this part.
#   3. Installs the system libraries Chromium links against. THIS step
#      requires sudo — Playwright runs `apt-get install -y ...` for libs
#      like libnss3, libatk-bridge2.0-0, libdrm2, etc. You'll be prompted
#      for your sudo password.
#
# Run with: bash scripts/install-playwright.sh
#       or: ./scripts/install-playwright.sh   (after chmod +x)
#
# Idempotent — safe to re-run.

set -euo pipefail

# Resolve repo root from the script's own location so the script works no
# matter where it's invoked from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend"

echo "==> repo root: $REPO_ROOT"
echo "==> frontend:  $FRONTEND_DIR"

if [ ! -d "$FRONTEND_DIR" ]; then
  echo "ERROR: frontend/ not found at $FRONTEND_DIR" >&2
  exit 1
fi

cd "$FRONTEND_DIR"

# ----- 1. npm dep -----
echo
echo "==> [1/3] Installing @playwright/test (devDep)..."
if [ -f package.json ] && grep -q '"@playwright/test"' package.json; then
  echo "    already in package.json — running install to sync"
fi
npm install --save-dev --no-audit --no-fund @playwright/test

# ----- 2. Chromium browser (no sudo) -----
echo
echo "==> [2/3] Downloading Chromium browser into ~/.cache/ms-playwright..."
npx --yes playwright install chromium

# ----- 3. System libraries (needs sudo) -----
echo
echo "==> [3/3] Installing system libraries Chromium needs (requires sudo)..."
echo "    You will likely be prompted for your password."
if command -v sudo >/dev/null 2>&1; then
  sudo npx --yes playwright install-deps chromium
else
  echo "    sudo not available — running without (will fail if libs are missing):"
  npx --yes playwright install-deps chromium
fi

# ----- Sanity check -----
echo
echo "==> Verifying installation..."
npx --yes playwright --version
echo "    Chromium binary:"
find "$HOME/.cache/ms-playwright" -maxdepth 2 -name 'chrome' -type f 2>/dev/null | head -1 \
  || echo "    (chrome binary not found — install may have failed silently)"

echo
echo "DONE. Next steps:"
echo "  - Tell Claude: 'continue with Phase 2.5 — Playwright is installed'"
echo "  - Or run a quick smoke test yourself:"
echo "      cd $FRONTEND_DIR && npx playwright open http://localhost:8001/api/health"
