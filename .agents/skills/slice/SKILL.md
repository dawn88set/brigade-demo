---
name: slice
description: Cut the approved plan on an intent issue into small, independent agent:ready issues in the exact format the adapter and planner read. Idempotent. No code changes.
schedule: When an intent issue is labeled plan:ready and not yet sliced.
---

# Slice

You turn the approved plan on intent #N into issues that agents can build in parallel without colliding. You write no code.

## 1. Read
- `gh issue view <N> --comments`. Use the **latest** comment that starts with `<!-- brigade:plan -->`, plus any maintainer comments after it; those win.
- **Idempotency:** list existing children with `gh issue list --state all --search "\"Part of #<N>\" in:body" --json number,title`. Create only the slices that are missing.

## 2. Cut
Each issue must be:
- **small:** under about 400 changed lines, one reviewable idea;
- **independent where possible:** declare a real dependency with `Blocked by #M`, and nothing more;
- **path-honest:** `Touches:` lists the globs it will change. The planner won't run two issues with overlapping `Touches:` at the same time, so tight globs mean more parallelism, and globs that are too tight make the build go out of scope;
- **provable:** the verification line names the journey, spec or command a verifier will use.

Create the issues in dependency order, so the `Blocked by #M` references point at real issue numbers.

## 3. Issue format (the adapter parses this; keep the field names exactly)

```
Part of #<N>

## Outcome
<one or two sentences, user-visible>

## Acceptance criteria
- [ ] ...

Touches: <glob>, <glob>
Blocked by #<M>            (omit when none)

## Verification
<journey / spec / command and what "working" looks like>
```

Create each with:
```
gh issue create --title "<imperative title>" --body-file <file> --label agent:ready --label risk:<low|medium|high>
```
Pick the risk from `brigade.toml` `[risk]`: `human`/`high` paths mean high, `medium` paths mean medium, otherwise low. A slice that touches `[risk].human` paths also gets `--label needs-human`.

## 4. Hand off
- Comment on #N with the list of created issues and their dependencies.
- Add the label: `gh issue edit <N> --add-label sliced`.
- Emit `stage_yield` with one line: how many issues you created and how many can start now.

## Never
- Edit files, commit or open PRs.
- Change the plan's scope. If the plan can't be sliced as written, comment why on #N, add `needs-decision`, and stop.
