#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

PROJECT_DIR="$HOME/AtriaTrade"
BACKUP_DIR="$HOME/storage/shared/Download/AtriaTrade_Backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE_PATH="$BACKUP_DIR/AtriaTrade_$TIMESTAMP.tar.gz"
CHECKSUM_PATH="$ARCHIVE_PATH.sha256"
INFO_PATH="$BACKUP_DIR/AtriaTrade_${TIMESTAMP}_backup_info.txt"

trap 'echo "[FAILED] Backup stopped at line $LINENO."; exit 1' ERR

cd "$PROJECT_DIR"

if [ ! -d .git ] || [ ! -d src ] || [ ! -d tests ]; then
    echo "[FAILED] AtriaTrade Git repository, src, or tests directory is missing."
    exit 1
fi

if [ ! -d "$HOME/storage/shared" ]; then
    echo "[FAILED] Shared storage is not available. Run termux-setup-storage and allow access."
    exit 1
fi

mkdir -p "$BACKUP_DIR"

echo "[1/7] Checking for tracked secret files..."
SENSITIVE_FILES="$(git ls-files | grep -E '(^|/)(\.env|id_rsa|id_ed25519|.*\.pem|.*\.key)$' | grep -vE '(^|/)\.env\.example$' || true)"
if [ -n "$SENSITIVE_FILES" ]; then
    echo "[FAILED] Potential secret files are tracked:"
    printf '%s\n' "$SENSITIVE_FILES"
    echo "Remove secrets before pushing."
    exit 1
fi

echo "[2/7] Running the complete test suite..."
python -m pytest -q

echo "[3/7] Preparing Git ignore rules..."
touch .gitignore
for RULE in ".env" ".env.*" "!.env.example" "venv/" ".venv/" "__pycache__/" "*.py[cod]" ".pytest_cache/" "*.log" "*.sqlite3" "*.db" "backups/"
do
    grep -Fxq "$RULE" .gitignore || printf '%s\n' "$RULE" >> .gitignore
done

echo "[4/7] Creating Git commit..."
git add -A
if ! git diff --cached --quiet; then
    git commit -m "chore: verified full backup"
else
    echo "[INFO] No new changes to commit."
fi

BRANCH="$(git branch --show-current)"
if [ -z "$BRANCH" ]; then
    echo "[FAILED] Git is in detached HEAD state."
    exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
    echo "[FAILED] Git remote 'origin' is not configured."
    exit 1
fi

REMOTE_URL="$(git remote get-url origin)"
COMMIT="$(git rev-parse HEAD)"

echo "[5/7] Pushing to GitHub..."
git push -u origin "$BRANCH"

REMOTE_COMMIT="$(git ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}')"
if [ -z "$REMOTE_COMMIT" ] || [ "$COMMIT" != "$REMOTE_COMMIT" ]; then
    echo "[FAILED] GitHub commit verification failed."
    echo "Local:  $COMMIT"
    echo "Remote: $REMOTE_COMMIT"
    exit 1
fi

echo "[6/7] Creating and verifying mobile archive..."
tar \
    --exclude="./.git" \
    --exclude="./venv" \
    --exclude="./.venv" \
    --exclude="./.env" \
    --exclude="./.pytest_cache" \
    --exclude="*/__pycache__" \
    --exclude="*.pyc" \
    --exclude="*.pyo" \
    --exclude="*.log" \
    --exclude="*.tar.gz" \
    --exclude="*.zip" \
    -czf "$ARCHIVE_PATH" \
    -C "$PROJECT_DIR" .

tar -tzf "$ARCHIVE_PATH" >/dev/null
sha256sum "$ARCHIVE_PATH" > "$CHECKSUM_PATH"
sha256sum -c "$CHECKSUM_PATH"

echo "[7/7] Writing backup details..."
{
    echo "Project: AtriaTrade"
    echo "Backup time: $(date -Iseconds)"
    echo "Git branch: $BRANCH"
    echo "Git commit: $COMMIT"
    echo "Git remote: $REMOTE_URL"
    echo "Archive: $ARCHIVE_PATH"
    echo "Checksum file: $CHECKSUM_PATH"
    echo "Test result: Complete test suite passed"
} > "$INFO_PATH"

echo ""
echo "[SUCCESS] Backup completed and verified."
echo "GitHub branch: $BRANCH"
echo "GitHub commit: $COMMIT"
echo "Mobile archive: $ARCHIVE_PATH"
echo "Checksum: $CHECKSUM_PATH"
echo "Backup details: $INFO_PATH"
ls -lh "$ARCHIVE_PATH" "$CHECKSUM_PATH" "$INFO_PATH"
