---
name: oops
description: The default branch is red. Find out why, and either open a revert PR for the merge that broke it or file one clear issue for a human. Always leaves an `oops-<sha7>` marker so it never loops.
schedule: When the newest commit on the default branch has a failed CI run with no open oops PR or issue.
---

# Oops

Main is red, and no new work starts until it's green. Be fast and conservative: **restore green first, fix forward later**.

## 1. Diagnose (read-only)
- Failed runs: `gh run list --branch <base> --limit 10`, then `gh run view <id> --log-failed | tail -200`.
- Classify the failure:
  - **Regression:** a test, build or check fails because of code on main. Find the culprit: the last green commit vs. this one (`git log --oneline <green>..<sha>`). Merged PRs are squash commits, so the culprit is usually one commit.
  - **External:** billing or quota ("recent account payments have failed"), a runner outage, a secret or permission problem, a third-party service down. No code change fixes these.
  - **Flaky:** passes on a re-run, or the failure has no relation to the change. Confirm by running the failing test locally (in this worktree) 3 times.

## 2. Act. Every outcome leaves exactly one marker whose title contains `oops-<sha7>`.
- **Regression from one commit:** run `git revert --no-edit <culprit>` in this worktree, then run the profile's fast check to confirm it's green locally. Write `.brigade/pr.md`:
  - **Why:** the failing job, the log excerpt, and the culprit.
  - **What changed:** "revert of #P".
  - **Verification:** what you ran.

  The loop opens the PR, titled with this order's title, which already contains `oops-<sha7>`: that's the marker. Comment on the culprit's original issue with the revert's reason, so it can be rebuilt correctly later.
- **External or flaky:** change no code. Run `gh issue create --label oops --label needs-human --title "main red: <one line> (oops-<sha7>)"`. The body has the classification, the evidence (log lines), and what a human must do (for example "fix billing at …").
- **Unclear:** treat it as external and file the issue. Don't guess-fix main.

## 3. Hand off
Emit `stage_yield` with the classification and the marker (PR branch or issue number).

## Never
- Push to the default branch, force-push, or disable or skip a failing test or check to get green.
- Re-run workflows (agents don't have that permission). Note it in the issue instead.
