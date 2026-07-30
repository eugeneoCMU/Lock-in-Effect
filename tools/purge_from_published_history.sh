#!/usr/bin/env bash
# Purge working notes (and, optionally, the Freddie loan-level parquets) from the
# repository's PUBLISHED history.
#
# THIS SCRIPT IS NOT RUN BY ANY AGENT. It rewrites published history and requires a
# force-push. It is written to be read first, then run by Eugene, deliberately.
#
# It refuses to run unless you set I_HAVE_READ_THE_WARNINGS=1.

set -euo pipefail

if [[ "${I_HAVE_READ_THE_WARNINGS:-0}" != "1" ]]; then
  cat <<'WARN'
REFUSING TO RUN. Read this first.

WHAT THIS DOES
  Removes the listed paths from EVERY commit in history, rewrites every commit
  hash, and requires `git push --force`.

WHY YOU MAY NOT NEED IT
  Of the 24 working-note files, 7 were never pushed. Those were untracked before
  any push and will never reach GitHub -- no rewrite required for them. This
  script only matters for the 17 that are already in origin/main.

FOUR THINGS THAT BREAK, AND ONE THAT DOES NOT
  1. Appendix A of the paper cites four commit hashes -- ad52db6, 651d1a0,
     d0ef130, 57181b3 -- as evidence that spec commits precede result commits.
     ALL FOUR CHANGE. Edit the paper BEFORE you rewrite, or those citations point
     at nothing.
  2. Appendix A also says the spec-before-run ordering is "verifiable from git
     history". A rewrite preserves parent order, so the ORDERING claim survives,
     but every hash a reader might check against is different.
  3. Anyone who has already cloned or forked keeps the old objects. GitHub also
     serves cached blobs by SHA until you ask Support to purge them.
  4. All 79 unpushed commits are rewritten too.
  NOT broken: no gate and no test reads any of these files. The suite is
  unaffected either way -- this is about what is published, not what works.

DO IT ONCE, IF AT ALL
  C-132 (the Freddie loan-level parquets, a licensing exposure) is the only
  reason here with real stakes. If you are going to rewrite history, do that and
  this in ONE pass. Two force-pushes is two chances to lose something.

STRONGLY RECOMMENDED FIRST
  git bundle create ~/lockin-before-rewrite.bundle --all

Then re-run with:  I_HAVE_READ_THE_WARNINGS=1 tools/purge_from_published_history.sh
WARN
  exit 1
fi

command -v git-filter-repo >/dev/null 2>&1 || {
  echo "git-filter-repo not found.  pip install git-filter-repo" >&2; exit 1; }

# --- what goes -------------------------------------------------------------
# Working notes only. specs/, TECHNICAL.md, SPEC_danish_redemption_validation and
# OOS_IDENTIFICATION.md are DELIBERATELY ABSENT: the paper's App. A cites specs/,
# and the other three are the provenance record, not coordination chatter.
PATHS=(
  --path-glob 'HANDOFF_*.md'
  --path-glob 'PLAN_*.md'
  --path-glob 'REVIEW_*.md'
  --path-glob 'REVIEW2_*.md'
  --path-glob 'REVIEW3_*.md'
  --path-glob 'REREVIEW_*.md'
  --path-glob 'revision_roadmap_*.md'
  --path timing_sweep_log.md
  --path docs/carroll_round_qa_prep.md
  --path-glob 'docs/superpowers/*'
)

# Uncomment to fold C-132 into the same pass (recommended if doing this at all):
# PATHS+=( --path hazard/data/loan_sample.parquet
#          --path hazard/data/cohort_month_panel.parquet )

echo "Rewriting history to remove:"
printf '  %s\n' "${PATHS[@]}"
echo
read -r -p "Type REWRITE to proceed: " confirm
[[ "$confirm" == "REWRITE" ]] || { echo "aborted"; exit 1; }

git filter-repo --invert-paths "${PATHS[@]}"

cat <<'NEXT'

Rewrite complete. Nothing has been pushed.

NEXT STEPS, in order:
  1. Inspect:  git log --oneline | head -20
               git log --all --name-only | grep -c HANDOFF   # expect 0
  2. Re-add the remote (filter-repo drops it deliberately):
       git remote add origin https://github.com/eugeneoCMU/Lock-in-Effect.git
  3. Force-push ONLY when you are satisfied:
       git push --force --all
       git push --force --tags
  4. Email GitHub Support to purge cached objects and any forks.
  5. Re-verify the suite, since every hash moved:
       python3 tools/liveness_gates.py | tail -1
       python3 -m pytest tests/ -q | tail -1
NEXT
