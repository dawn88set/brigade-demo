# brigade-demo

## How work happens
- Changes reach `main` only through pull requests. Autonomous agents (Brigade) build `agent:ready` issues;
  an independent verifier and a reviewer must pass, plus `ci-gate`, before GitHub merges.
- Product intent: open an issue labeled `intent`. Agents shape it into a plan, slice it into issues, build,
  verify, review and merge. Questions come back as `needs-decision` issues.
- Paths in `.github/CODEOWNERS` need the maintainer's approval.

## Rules for every change (humans and agents)
- Tests first: a failing test that encodes the acceptance criteria, then the code.
- `pnpm run verify` must pass (lint, typecheck, test, build).
- Never weaken a test, check, threshold or lint rule to get green. Fix the cause.
- No `any`, no dead code, no commented-out code, no speculative abstractions. Delete before adding.
- Never commit secrets or read `.env` files.

## Commands
- `pnpm install` · `pnpm run verify` · `pnpm test` · `pnpm run build`
