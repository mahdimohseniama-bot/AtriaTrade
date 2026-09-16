import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from src.web.app import app
    print("=" * 50)
    print("REGISTERED ROUTES:")
    for r in app.routes:
        methods = getattr(r, "methods", None) or {"MOUNT/WS"}
        # فیلتر کردن روت‌های سیستمی و تمرکز روی apiها
        path = getattr(r, "path", "")
        if path.startswith("/api"):
            print(f"  {sorted(list(methods))}  {path}")
    print("=" * 50)
except Exception as e:
    print(f"IMPORT FAILED: {type(e).__name__}: {e}")
