---
name: schedule
description: Brigade scheduler. Runs the deterministic planner and writes its orders. One command, no code changes, no merging.
schedule: When the backlog or open-PR state changed, or after a stage failed. The loop throttles this to [schedule] min_interval.
---

# Schedule

Your whole job is one command. The planning rules live in code, so every scheduler run costs almost nothing of the plan's usage. Code also doesn't drift.

1. From the project root, run:

   ```
   python3 ~/.brigade/kit/plan_orders.py > .noodle/orders-next.json
   ```

2. Check that the file is valid JSON with an `orders` key. Use `python3 -m json.tool .noodle/orders-next.json > /dev/null`.
3. Stop. Don't add, remove or reorder orders. Don't read code. Don't start any other work.

If the command fails, don't improvise orders. Write `{"orders": []}` to `.noodle/orders-next.json` and report the error in one line. An empty schedule is safe; a guessed one isn't.

## What the planner decides (for reference; don't redo it)
- **Finish before starting.** It picks babysit for a red PR first, then review for a verified PR, then verify for an unverified PR. Oldest PR first; one follow-up per PR at a time.
- **Then ready issues.** Only unblocked ones from maintainers, whose declared `Touches:` paths don't overlap work in flight or open PRs.
- **Limits.**
  - Never more orders than free agent slots. The governor sets those from memory and plan usage.
  - Never more verify runs than `[verify].max_parallel`.
- **Models by role and risk.** Defaults can be overridden in `brigade.toml` under `[models]`.
  - Opus: execute, high-risk verify, high-risk review.
  - Sonnet: other verify and review, and babysit.
- **Labels.** Issues labeled `needs-decision`, `blocked` or `needs-human` go to `action_needed`.
