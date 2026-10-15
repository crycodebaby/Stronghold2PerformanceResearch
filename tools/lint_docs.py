"""Docs linter (run by .githooks/pre-push; also usable by hand).

Usage: python -I tools/lint_docs.py [--range <git rev range>]

Checks (exit 1 on any error):
  ids      F###, D###, EXP-### defined at most once (table first cell / D### heading)
  links    relative Markdown links in *.md point to existing files
  summary  every docs/**/*.md has a "> Kurzfassung:" line within its first 4 lines
  size     line limits: CLAUDE.md 80, SKILL.md 100, docs/**/*.md 300
  paths    no absolute user paths (C:\\Users\\...) in any *.md or data/ file
  state    with --range: docs/STATE.md changed in the range
"""
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

REPO = paths.REPO
ID_DEFS = [
    ("docs/FINDINGS.md", re.compile(r"^\|\s*(F\d{3})\s*\|", re.M)),
    ("docs/DECISIONS.md", re.compile(r"^##\s+(D\d{3})\b", re.M)),
    ("docs/EXPERIMENTS.md", re.compile(r"^\|\s*(EXP-\d{3}[a-z]?)\s*\|", re.M)),
]
LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
USER_PATH = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s]+", re.I)
SKIP_DIRS = {".git", "captures", "build", "__pycache__"}


def md_files():
    for p in REPO.rglob("*.md"):
        if not SKIP_DIRS.intersection(p.relative_to(REPO).parts):
            yield p


def check_ids(errors):
    for rel, rx in ID_DEFS:
        f = REPO / rel
        if not f.exists():
            continue
        for ident, n in Counter(rx.findall(f.read_text(encoding="utf-8"))).items():
            if n > 1:
                errors.append(f"ids: {ident} defined {n}x in {rel}")


def check_links(errors):
    for f in md_files():
        text = INLINE_CODE.sub("", f.read_text(encoding="utf-8"))
        for target in LINK.findall(text):
            if re.match(r"^[a-z]+:", target):
                continue  # http:, mailto:
            if not (f.parent / target).exists():
                errors.append(f"links: {f.relative_to(REPO)} -> {target} (missing)")


def check_summary(errors):
    for f in (REPO / "docs").rglob("*.md"):
        head = f.read_text(encoding="utf-8").splitlines()[:4]
        if not any(line.startswith("> Kurzfassung:") for line in head):
            errors.append(f"summary: {f.relative_to(REPO)} lacks '> Kurzfassung:' in first 4 lines")


def check_size(errors):
    for f in md_files():
        rel = f.relative_to(REPO)
        limit = 80 if f.name == "CLAUDE.md" else 100 if f.name == "SKILL.md" else \
            300 if rel.parts[0] == "docs" else None
        n = len(f.read_text(encoding="utf-8").splitlines())
        if limit and n > limit:
            errors.append(f"size: {rel} has {n} lines (limit {limit})")


def check_paths(errors):
    files = set(md_files())
    for f in (REPO / "data").rglob("*"):
        if f.is_file() and f.suffix in (".jsonl", ".json", ".csv"):
            files.add(f)
    for f in sorted(files):
        if USER_PATH.search(f.read_text(encoding="utf-8", errors="replace")):
            errors.append(f"paths: absolute user path in {f.relative_to(REPO)}")


def check_state(errors, rev_range):
    out = subprocess.run(["git", "log", "--format=", "--name-only", *rev_range.split(), "--", "docs/STATE.md"],
                         cwd=REPO, capture_output=True, text=True).stdout
    if "docs/STATE.md" not in out:
        errors.append("state: no commit in the pushed range updates docs/STATE.md")


def main():
    errors = []
    check_ids(errors)
    check_links(errors)
    check_summary(errors)
    check_size(errors)
    check_paths(errors)
    if "--range" in sys.argv:
        check_state(errors, sys.argv[sys.argv.index("--range") + 1])
    for e in errors[:30]:
        print(f"lint_docs: {e}", file=sys.stderr)
    if len(errors) > 30:
        print(f"lint_docs: ... {len(errors) - 30} more", file=sys.stderr)
    print(f"lint_docs: {'FAIL' if errors else 'OK'} ({len(errors)} error(s))")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
