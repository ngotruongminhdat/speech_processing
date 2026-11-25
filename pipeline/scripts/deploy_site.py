#!/usr/bin/env python3
"""Deploy thư viện lên GitHub Pages (branch gh-pages). Chạy lại mỗi khi xong thêm
một chương hay một cuốn: chỉ phần thay đổi được đẩy lên.

Các bước:
  1. build_site.py lắp lại site/ từ mọi sách trong books/
  2. chép site/ vào worktree .deploy/ (branch gh-pages)
  3. giữ nguyên thư mục build/ của đồ án giữa kỳ (lấy từ branch mid_term_project)
     để các đường dẫn đã nộp, ví dụ .../build/index.html, không bị hỏng
  4. commit "Deploy: N sách, R/T phần" và push

Usage: python3 pipeline/scripts/deploy_site.py [--no-push] [--no-legacy]
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SITE, DEPLOY = REPO / "site", REPO / ".deploy"
BRANCH, LEGACY_BRANCH = "gh-pages", "mid_term_project"


def git(*args, cwd=REPO, check=True, capture=False):
    return subprocess.run(["git", *args], cwd=cwd, check=check, text=True,
                          capture_output=capture)


def main(push: bool, legacy: bool):
    build = [sys.executable, str(REPO / "pipeline" / "scripts" / "build_site.py")]
    subprocess.run(build + (["--legacy-totto"] if legacy else []), check=True)

    if not (DEPLOY / ".git").exists():
        exists = git("rev-parse", "--verify", "--quiet", BRANCH, check=False, capture=True).returncode == 0
        if exists:
            git("worktree", "add", str(DEPLOY), BRANCH)
        else:
            git("worktree", "add", "--orphan", "-b", BRANCH, str(DEPLOY))

    # thay toàn bộ nội dung cũ bằng site/ mới, trừ .git và build/ (trang giữa kỳ)
    for p in DEPLOY.iterdir():
        if p.name in (".git", "build"):
            continue
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    shutil.copytree(SITE, DEPLOY, dirs_exist_ok=True)
    if legacy and not (DEPLOY / "build" / "index.html").exists():
        git("checkout", LEGACY_BRANCH, "--", "build", cwd=DEPLOY)

    git("add", "-A", cwd=DEPLOY)
    if git("diff", "--cached", "--quiet", cwd=DEPLOY, check=False).returncode == 0:
        print("Không có gì thay đổi so với lần deploy trước.")
        return
    books = json.loads((SITE / "catalog.json").read_text(encoding="utf-8"))["books"]
    units = [u for b in books for u in b.get("units", [])]
    ready = sum(1 for u in units if u["ready"])
    git("commit", "-q", "-m", f"Deploy: {len(books)} sách, {ready}/{len(units)} phần đã có audio", cwd=DEPLOY)
    print(git("log", "--oneline", "-1", cwd=DEPLOY, capture=True).stdout.strip())
    if push:
        git("push", "-u", "origin", BRANCH, cwd=DEPLOY)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-push", action="store_true", help="chỉ commit vào gh-pages, chưa đẩy lên")
    ap.add_argument("--no-legacy", action="store_true", help="không kèm trang Totto-chan của giữa kỳ")
    a = ap.parse_args()
    main(push=not a.no_push, legacy=not a.no_legacy)
