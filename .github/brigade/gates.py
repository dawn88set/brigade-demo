#!/usr/bin/env python3
"""Deterministic PR gates: risk labelling and gate integrity.

    gates.py risk      --base <ref> [--head <ref>] [--repo <dir>]   -> JSON {risk, needs_human, reasons}
    gates.py integrity --base <ref> [--head <ref>] [--repo <dir>]   -> JSON {violations, warnings}; exit 1 on violations

Both read their rules from the project's brigade.toml ([risk], [gates]) and run
in CI, so no agent decides its own risk or grades its own test changes.
Python 3.11+, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

# ---------------------------------------------------------------------------- globbing


@lru_cache(maxsize=512)
def _glob_re(pattern: str) -> re.Pattern:
    i, out = 0, []
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def matches(path: str, patterns: list[str]) -> str | None:
    for p in patterns:
        if _glob_re(p).match(path):
            return p
    return None


# ---------------------------------------------------------------------------- diff model


@dataclass
class FileDiff:
    path: str
    status: str  # A, M, D, R
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


def parse_unified(diff: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    cur: FileDiff | None = None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            m = re.match(r"diff --git a/(.+) b/(.+)$", line)
            cur = FileDiff(path=m.group(2) if m else line, status="M")
            files.append(cur)
        elif cur is None:
            continue
        elif line.startswith("new file mode"):
            cur.status = "A"
        elif line.startswith("deleted file mode"):
            cur.status = "D"
        elif line.startswith("rename from "):
            cur.status = "R"
        elif line.startswith("+++ ") or line.startswith("--- "):
            continue
        elif line.startswith("+"):
            cur.added.append(line[1:])
        elif line.startswith("-"):
            cur.removed.append(line[1:])
    return files


def git_diff(repo: Path, base: str, head: str) -> list[FileDiff]:
    out = subprocess.run(["git", "-C", str(repo), "diff", "--no-color", "-M", f"{base}...{head}"],
                         capture_output=True, text=True, check=True).stdout
    return parse_unified(out)


# ---------------------------------------------------------------------------- risk

RANK = {"low": 0, "medium": 1, "high": 2}


def assess_risk(files: list[FileDiff], rules: dict) -> dict:
    human, high, medium = rules.get("human", []), rules.get("high", []), rules.get("medium", [])
    content = [re.compile(p) for p in rules.get("human_content", [])]
    risk, needs_human, reasons = "low", False, []
    for f in files:
        if (p := matches(f.path, human)):
            needs_human = True
            reasons.append(f"{f.path}: human-gated ({p})")
            risk = "high"
        elif (p := matches(f.path, high)):
            reasons.append(f"{f.path}: high ({p})")
            risk = max(risk, "high", key=RANK.get)
        elif matches(f.path, medium):
            risk = max(risk, "medium", key=RANK.get)
        for rx in content:
            hit = next((l for l in f.added + f.removed if rx.search(l)), None)
            if hit:
                needs_human = True
                risk = "high"
                reasons.append(f"{f.path}: content rule {rx.pattern!r} matched: {hit.strip()[:80]}")
    size = sum(len(f.added) + len(f.removed) for f in files)
    if size > rules.get("large_diff_lines", 600) and risk == "low":
        risk = "medium"
        reasons.append(f"large diff ({size} lines)")
    return {"risk": risk, "needs_human": needs_human, "reasons": reasons, "lines": size}


# ---------------------------------------------------------------------------- integrity

TEST_FILE = [r"(^|/)(test|tests|__tests__|e2e|spec)/", r"\.(test|spec)\.[cm]?[jt]sx?$", r"(^|/)test_[^/]+\.py$",
             r"_test\.(py|go)$"]
TEST_CASE = re.compile(r"^\s*(?:(?:it|test|describe)(?:\.each\([^)]*\))?\s*\(|def test_\w+|func Test\w+\(|"
                       r"async def test_\w+)")
SKIP = re.compile(r"(?:\b(?:it|test|describe)\.(?:skip|only|todo)\s*\(|\bx(?:it|describe|test)\s*\(|"
                  r"\bf(?:it|describe)\s*\(|@pytest\.mark\.(?:skip|xfail)|\bt\.Skip(?:Now|f)?\(|"
                  r"\bunittest\.skip|\.only\s*\()")
SUPPRESS = re.compile(r"(eslint-disable|@ts-ignore|@ts-expect-error|@ts-nocheck|#\s*noqa|#\s*type:\s*ignore|"
                      r"//\s*nolint|#\s*pragma:\s*no\s*cover|istanbul ignore|c8 ignore|biome-ignore)")


def is_test_file(path: str) -> bool:
    return any(re.search(p, path) for p in TEST_FILE)


# The gate's own source contains the patterns it looks for. It is human-gated by path
# (CODEOWNERS on .github/), so its content is not scanned.
CONTENT_EXEMPT = [".github/brigade/**", "**/kit/gates/**", "**/kit/tests/test_gates.py"]


def check_integrity(files: list[FileDiff], rules: dict) -> dict:
    protected = rules.get("protected", [])
    exempt = CONTENT_EXEMPT + rules.get("content_exempt", [])
    violations, warnings = [], []
    for f in files:
        if (p := matches(f.path, protected)):
            violations.append(f"{f.path}: protected file changed ({p})")
        if matches(f.path, exempt):
            continue
        if is_test_file(f.path):
            if f.status == "D":
                violations.append(f"{f.path}: test file deleted")
            removed = sum(1 for l in f.removed if TEST_CASE.match(l))
            added = sum(1 for l in f.added if TEST_CASE.match(l))
            if removed > added:
                violations.append(f"{f.path}: {removed - added} test case(s) removed")
            removed_asserts = sum(1 for l in f.removed if re.search(r"\b(expect|assert)\w*\b", l))
            added_asserts = sum(1 for l in f.added if re.search(r"\b(expect|assert)\w*\b", l))
            if removed_asserts > added_asserts + rules.get("assert_slack", 0):
                warnings.append(f"{f.path}: {removed_asserts - added_asserts} fewer assertion line(s)")
        for l in f.added:
            if SKIP.search(l):
                violations.append(f"{f.path}: skip/only added: {l.strip()[:80]}")
            elif SUPPRESS.search(l):
                (violations if rules.get("suppressions_block") else warnings).append(
                    f"{f.path}: suppression added: {l.strip()[:80]}")
    return {"violations": violations, "warnings": warnings}


# ---------------------------------------------------------------------------- cli


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["risk", "integrity"])
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--repo", default=".")
    a = ap.parse_args(argv)
    repo = Path(a.repo)
    prof_file = repo / "brigade.toml"
    prof = tomllib.loads(prof_file.read_text()) if prof_file.exists() else {}
    files = git_diff(repo, a.base, a.head)
    if a.mode == "risk":
        print(json.dumps(assess_risk(files, prof.get("risk", {})), indent=2))
        return 0
    res = check_integrity(files, prof.get("gates", {}))
    print(json.dumps(res, indent=2))
    return 1 if res["violations"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
