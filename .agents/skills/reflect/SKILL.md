---
name: reflect
description: Learn from recent merged agent PRs. Turn repeated mistakes into checks first and notes last, in one small PR a human approves. Marks the PRs reflected.
schedule: When enough merged agent PRs have not been reflected on yet (the adapter decides).
---

# Reflect

You make the kitchen better at its job. Recurring mistakes must become harder to repeat, enforced by machines where possible.

## 1. Gather evidence (for each PR in the order's list)
- `gh pr view <P> --json title,body,labels,reviews,comments,commits`
- The verifier and review check summaries: `gh pr checks <P>`, plus the check-run text.
- How many babysit rounds it took (`babysit:*` labels), CI failures, and whether it was later reverted (`gh search prs --repo <repo> "Revert" "#<P>"`).

## 2. Find patterns, not anecdotes
A lesson needs **at least 2** occurrences, or one costly one (a revert, a red main, a verifier FAIL that reached review). For each lesson: what happened, how often, what it cost, and the root cause.

## 3. Encode, strongest first (pstack's fix hierarchy)
1. **Architecture or types** that make the mistake impossible.
2. **A lint rule, ast-grep rule or CI check.**
3. **A test.**
4. **Prose last:** a line in `.agents/skills/<skill>/references/lessons.md`, or a fix to the verifier feature map (`[verify].feature_map`).

For 1–3, if the fix is real code, file an issue with `gh issue create --label agent:ready --label risk:<…>`, in `slice`'s format, rather than coding it here. For 4, edit the files in this worktree.

Keep each `lessons.md` under about 40 lines: merge duplicates, and delete lessons that are now enforced by a check.

## 4. Hand off
- Commit the prose and feature-map edits (one commit, `docs(agents): lessons from #a, #b, …`). Write `.brigade/pr.md` with Why, What changed (one line per lesson, with evidence links) and Verification (n/a: docs only).

  The loop opens the PR. `.agents/` is code-owned, so a human approves it. That's intended: the kitchen can't change its own rules alone.
- Mark every PR in the list: `gh pr edit <P> --add-label reflected`.
- If there's nothing worth encoding, still mark the PRs and commit nothing.
- Emit `stage_yield`: the number of lessons, issues filed, and whether a PR is pending.

## Never
- Weaken a check, test or gate.
- Edit skills' `SKILL.md` files (propose the change in the PR body instead).
