#!/usr/bin/env bash
# Capture the raw output of the four baseline tools on every planted folder (never the held-out set).
# Needs Docker, the image from baselines/tools/Dockerfile (docker build -t acr-baselines:m52 baselines/tools),
# and a local clone of the semgrep-rules repository at the commit in baselines/semgrep/PINS.md, path in $RULES.
# Semgrep and pgrls run with --network none. rlsautotest runs on an --internal network (see its driver).
set -u
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")/.."
ROOT=$(pwd -W 2>/dev/null || pwd)
OUT=tests/fixtures/baselines
mkdir -p $OUT/semgrep $OUT/pgrls $OUT/advisors $OUT/rlsautotest
for dir in planted/*/*/migrations planted/*/migrations; do
  app=$(echo "$dir" | cut -d/ -f2); side=$(echo "$dir" | cut -d/ -f3)
  [ -n "${ONLY:-}" ] && ! echo "$app" | grep -q -E "$ONLY" && continue
  [ "$app" = hostile-01-callout ] && continue
  name=${app}__${side}
  docker run --rm --network none -v "$ROOT/planted:/work/planted:ro" -v "$RULES:/rules:ro" -w /work acr-baselines:m52 \
    semgrep scan --config /rules/generic --metrics off --disable-version-check --json --quiet "$dir" \
    > $OUT/semgrep/$name.json 2>/dev/null
  docker run --rm --network none -v "$ROOT/planted:/work/planted:ro" -w /work acr-baselines:m52 \
    pgrls lint --sql-file "$(ls "$dir"/*.sql | head -1)" --format json > $OUT/pgrls/$name.json 2>/dev/null
  python baselines/advisors/run_splinter.py "$dir" > $OUT/advisors/$name.csv
  python baselines/rlsautotest/run_rlsautotest.py "$dir" > $OUT/rlsautotest/$name.json
done
