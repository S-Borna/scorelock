#!/usr/bin/env bash
# ── ScoreLock Production Smoke Test ──────────────────────
# Usage:
#   ./infra/smoke-test.sh                        # default: scorelock.saidborna.com
#   ./infra/smoke-test.sh http://localhost:8000   # local backend
#   ./infra/smoke-test.sh https://custom.url.com  # custom URL
#
# Tests the entire API surface to verify deployment health.

set -euo pipefail

BASE_URL="${1:-https://scorelock.saidborna.com}"
PASS=0
FAIL=0
TOTAL=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

check() {
    local name="$1"
    local path="$2"
    local expected="${3:-200}"
    TOTAL=$((TOTAL + 1))

    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${BASE_URL}${path}" 2>/dev/null || echo "000")

    if [[ "$status" == "$expected" ]]; then
        echo -e "  ${GREEN}✓${NC} ${name} (${status})"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}✗${NC} ${name} — expected ${expected}, got ${status}"
        FAIL=$((FAIL + 1))
    fi
}

echo ""
echo "🔍 ScoreLock Smoke Test"
echo "   Target: ${BASE_URL}"
echo "   Time:   $(date)"
echo ""

echo "── Core ──────────────────────────────────────────────"
check "Health check"          "/api/v1/health"
check "Leagues"               "/api/v1/leagues"
check "Fixtures (scheduled)"  "/api/v1/fixtures?status=scheduled"
check "Fixtures (finished)"   "/api/v1/fixtures?status=finished"

echo ""
echo "── Analysis ────────────────────────────────────────────"
check "Predictions"           "/api/v1/predictions/upcoming"
check "Value bets"            "/api/v1/value-bets"
check "Standings (PL)"        "/api/v1/standings/39"
check "Sentiments"            "/api/v1/sentiments"

echo ""
echo "── Content ─────────────────────────────────────────────"
check "Articles"              "/api/v1/articles?limit=5"

echo ""
echo "── Tipping League ──────────────────────────────────────"
check "Leaderboard"           "/api/v1/leaderboard"
check "Weekly top tipper"     "/api/v1/tips/weekly-top"

echo ""
echo "── Affiliate ───────────────────────────────────────────"
check "Affiliate links"       "/api/v1/affiliate/links"

echo ""
echo "── Auth (should reject) ────────────────────────────────"
check "Protected endpoint"    "/api/v1/tips/mine"    "401"

echo ""
echo "── Prometheus ──────────────────────────────────────────"
check "Metrics"               "/metrics"

echo ""
echo "═══════════════════════════════════════════════════════"
if [[ $FAIL -eq 0 ]]; then
    echo -e "  ${GREEN}All ${TOTAL} checks passed!${NC} 🚀"
else
    echo -e "  ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC} out of ${TOTAL}"
fi
echo "═══════════════════════════════════════════════════════"
echo ""

exit "$FAIL"
