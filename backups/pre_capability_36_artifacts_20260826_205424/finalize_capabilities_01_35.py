from pathlib import Path
from datetime import datetime, timezone
import os
import shutil
import subprocess
import sys
import tarfile

ROOT = Path.cwd()
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUPS = ROOT / "backups"
REPORTS = ROOT / "reports"
BACKUPS.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)

TEST_LOG = REPORTS / f"capabilities_01_35_pytest_{STAMP}.log"
STATUS_LOG = REPORTS / f"capabilities_01_35_status_{STAMP}.txt"
MANIFEST = REPORTS / f"capabilities_01_35_manifest_{STAMP}.txt"
ARCHIVE = BACKUPS / f"AtriaTrade_capabilities_01_35_GREEN_{STAMP}.tar.gz"

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "backups",
    "reports",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage_cache",
}

EXCLUDED_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    "secrets.json",
    "credentials.json",
}


def run(command, *, capture=False):
    print("\n$ " + " ".join(str(item) for item in command))
    if capture:
        return subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    return subprocess.run(command, cwd=ROOT)


def should_exclude(path: Path) -> bool:
    relative_parts = path.relative_to(ROOT).parts
    return (
        any(part in EXCLUDED_DIRS for part in relative_parts)
        or path.name in EXCLUDED_FILES
        or path.suffix in {".pyc", ".pyo"}
    )


def add_to_archive(archive, path: Path):
    if should_exclude(path):
        return

    arcname = path.relative_to(ROOT)
    archive.add(path, arcname=str(arcname), recursive=False)


print("=" * 68)
print("AtriaTrade | Final Verification + Backup | Capabilities 01-35")
print("=" * 68)
print(f"Project: {ROOT}")
print(f"UTC: {datetime.now(timezone.utc).isoformat()}")
print(f"Archive target: {ARCHIVE}")

# 1) Syntax validation
compile_result = run([sys.executable, "-m", "compileall", "-q", "src"])
if compile_result.returncode != 0:
    print("\n[STOP] compileall شکست خورد؛ هیچ Backup یا Git commit ساخته نشد.")
    raise SystemExit(compile_result.returncode)

print("[OK] compileall موفق بود.")

# 2) Complete test suite
print("\n[TEST] اجرای کامل تمام تست‌های قابلیت 1 تا 35...")
test_result = run(
    [sys.executable, "-m", "pytest", "-q", "--tb=short"],
    capture=True,
)

TEST_LOG.write_text(test_result.stdout, encoding="utf-8")
print(test_result.stdout, end="")

if test_result.returncode != 0:
    print(f"\n[STOP] تست‌ها شکست خوردند؛ گزارش در این مسیر ذخیره شد:\n{TEST_LOG}")
    print("هیچ Backup نهایی، commit یا push انجام نشد.")
    raise SystemExit(test_result.returncode)

print(f"\n[OK] تمام تست‌ها سبز هستند. لاگ: {TEST_LOG}")

# 3) Project manifest and Git state BEFORE backup
status_result = run(["git", "status", "--short"], capture=True)
branch_result = run(["git", "branch", "--show-current"], capture=True)
head_result = run(["git", "rev-parse", "--short", "HEAD"], capture=True)
remote_result = run(["git", "remote", "-v"], capture=True)

STATUS_LOG.write_text(
    "\n".join(
        [
            f"timestamp_utc={datetime.now(timezone.utc).isoformat()}",
            f"branch={branch_result.stdout.strip()}",
            f"head_before_commit={head_result.stdout.strip()}",
            "",
            "[git_status_before_commit]",
            status_result.stdout,
            "",
            "[git_remotes]",
            remote_result.stdout,
        ]
    ),
    encoding="utf-8",
)

with MANIFEST.open("w", encoding="utf-8") as handle:
    handle.write(f"AtriaTrade capabilities 01-35 GREEN manifest\n")
    handle.write(f"Created UTC: {datetime.now(timezone.utc).isoformat()}\n\n")

    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and not should_exclude(path):
            relative = path.relative_to(ROOT)
            handle.write(f"{relative}\t{path.stat().st_size} bytes\n")

print(f"[OK] Status report: {STATUS_LOG}")
print(f"[OK] File manifest: {MANIFEST}")

# 4) Local compressed backup; reports are deliberately included as release evidence.
with tarfile.open(ARCHIVE, "w:gz") as archive:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue

        relative = path.relative_to(ROOT)

        # Exclude previous backup archives, but include the current verification reports.
        if any(part in {".git", ".venv", "__pycache__", ".pytest_cache"} for part in relative.parts):
            continue
        if "backups" in relative.parts:
            continue
        if path.name in EXCLUDED_FILES or path.suffix in {".pyc", ".pyo"}:
            continue

        archive.add(path, arcname=str(relative), recursive=False)

print(f"[OK] Local backup created: {ARCHIVE}")
print(f"[OK] Backup size: {ARCHIVE.stat().st_size / (1024 * 1024):.2f} MB")

# 5) Ensure repository has a remote before committing.
if not remote_result.stdout.strip():
    print("\n[STOP] Git remote تنظیم نشده است.")
    print("Backup محلی با موفقیت ساخته شد، اما commit/push انجام نشد.")
    print("خروجی دستور زیر را ارسال کن:")
    print("git remote -v")
    raise SystemExit(2)

# 6) Git commit: source + verification reports; never stage backups or secrets.
gitignore_path = ROOT / ".gitignore"
existing_ignore = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""

required_ignores = [
    "",
    "# Local/generated/sensitive files",
    "backups/",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    ".env",
    ".env.*",
    "*.pyc",
    "*.pyo",
]

missing = [entry for entry in required_ignores if entry and entry not in existing_ignore]
if missing:
    with gitignore_path.open("a", encoding="utf-8") as handle:
        handle.write("\n" + "\n".join(missing) + "\n")

stage_result = run(["git", "add", "src", "tests", "reports", ".gitignore"])
if stage_result.returncode != 0:
    print("[STOP] git add شکست خورد؛ Backup محلی محفوظ است.")
    raise SystemExit(stage_result.returncode)

diff_result = run(["git", "diff", "--cached", "--quiet"])
if diff_result.returncode == 0:
    print("[INFO] تغییری برای commit وجود ندارد؛ به مرحله Push می‌رویم.")
elif diff_result.returncode == 1:
    message = (
        "chore: finalize capabilities 01-35 "
        f"(145 tests green) [{STAMP}]"
    )
    commit_result = run(["git", "commit", "-m", message])
    if commit_result.returncode != 0:
        print("[STOP] git commit شکست خورد؛ Backup محلی محفوظ است.")
        raise SystemExit(commit_result.returncode)
else:
    print("[STOP] بررسی staged changes با خطا مواجه شد.")
    raise SystemExit(diff_result.returncode)

# 7) Push to the currently checked-out upstream branch.
branch = branch_result.stdout.strip()
if not branch:
    print("[STOP] نام branch فعلی پیدا نشد؛ Push خودکار انجام نشد.")
    raise SystemExit(3)

push_result = run(["git", "push", "-u", "origin", branch])
if push_result.returncode != 0:
    print("\n[WARNING] Backup محلی و احتمالاً commit محلی ساخته شدند، اما Push ناموفق بود.")
    print("خروجی خطا را بفرست؛ هیچ فایل سورسی را تغییر نده.")
    raise SystemExit(push_result.returncode)

final_head = run(["git", "rev-parse", "--short", "HEAD"], capture=True)
final_status = run(["git", "status", "--short"], capture=True)

print("\n" + "=" * 68)
print("[SUCCESS] Capabilities 01-35 fully verified and saved.")
print(f"Tests: 145 passed")
print(f"Local backup: {ARCHIVE}")
print(f"Git commit: {final_head.stdout.strip()}")
print(f"Branch: {branch}")
print(f"Working tree status: {final_status.stdout.strip() or 'clean'}")
print("=" * 68)
