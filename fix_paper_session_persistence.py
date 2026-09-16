from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path.cwd()
TARGET = ROOT / "src" / "core" / "paper_session.py"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = ROOT / "backups" / f"paper_session_before_persistence_fix_{STAMP}.py"

if not TARGET.exists():
    raise FileNotFoundError(f"فایل پیدا نشد: {TARGET}")

BACKUP.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(TARGET, BACKUP)
print(f"[OK] Backup: {BACKUP}")

marker = "ATRIA_FINAL_PERSISTENCE_COMPAT"
text = TARGET.read_text(encoding="utf-8")

if marker not in text:
    patch = r'''

# ===== ATRIA_FINAL_PERSISTENCE_COMPAT =====
# سازگاری PaperSession با save/load/to_dict پس از پچ REMAINING6.

from datetime import datetime as _atria_persist_datetime, timezone as _atria_persist_timezone
from pathlib import Path as _atria_persist_Path
import json as _atria_persist_json


def _atria_persist_now():
    return (
        _atria_persist_datetime.now(_atria_persist_timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )


def _atria_persist_init(
    self,
    session_name="default_session",
    initial_capital=10000.0,
    currency="USDT",
    session_id=None,
    risk_config=None,
    data_dir=None,
    **kwargs,
):
    # پچ قبلی را صدا می‌زنیم تا قرارداد 10 تست هدف حفظ شود.
    _atria_final_paper_init(
        self,
        session_name=session_name,
        initial_capital=initial_capital,
        currency=currency,
        session_id=session_id,
        risk_config=risk_config,
        data_dir=data_dir,
        **kwargs,
    )

    # فیلدهایی که save()/to_dict() اصلی به آن‌ها متکی هستند.
    now = _atria_persist_now()
    self.created_at = kwargs.get("created_at", now)
    self.updated_at = kwargs.get("updated_at", self.created_at)


def _atria_persist_to_dict(self):
    return {
        "session_id": self.session_id,
        "session_name": self.session_name,
        "currency": self.currency,
        "initial_capital": float(self.initial_capital),
        "current_capital": float(self.current_capital),
        "total_pnl": float(getattr(self, "total_pnl", 0.0)),
        "created_at": self.created_at,
        "updated_at": self.updated_at,
        "trades": list(getattr(self, "trades", [])),
    }


def _atria_persist_save(self, file_path):
    path = _atria_persist_Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    self.updated_at = _atria_persist_now()

    path.write_text(
        _atria_persist_json.dumps(
            _atria_persist_to_dict(self),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


@classmethod
def _atria_persist_from_dict(cls, data):
    session = cls(
        session_name=data.get("session_name", "default_session"),
        initial_capital=float(data.get("initial_capital", 10000.0)),
        currency=data.get("currency", "USDT"),
        session_id=data.get("session_id"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )

    session.current_capital = float(
        data.get("current_capital", session.initial_capital)
    )
    session.total_pnl = float(data.get("total_pnl", 0.0))
    session.trades = list(data.get("trades", []))
    session.created_at = data.get("created_at", session.created_at)
    session.updated_at = data.get("updated_at", session.updated_at)
    return session


@classmethod
def _atria_persist_load(cls, file_path):
    path = _atria_persist_Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Session file not found: {path}")

    data = _atria_persist_json.loads(path.read_text(encoding="utf-8"))
    return cls.from_dict(data)


def _atria_persist_execute_trade(
    self,
    symbol,
    side,
    entry_price,
    exit_price,
    size=0.1,
    quantity=None,
    **kwargs,
):
    trade = _atria_final_execute_paper_trade(
        self,
        symbol=symbol,
        side=side,
        entry_price=entry_price,
        exit_price=exit_price,
        size=size,
        quantity=quantity,
        **kwargs,
    )

    self.updated_at = _atria_persist_now()

    # ذخیره خودکار با همان data_dir پچ قبلی
    if getattr(self, "data_dir", None):
        self.save(
            _atria_persist_Path(self.data_dir)
            / f"{self.session_name}.json"
        )

    return trade


PaperSession.__init__ = _atria_persist_init
PaperSession._now = staticmethod(_atria_persist_now)
PaperSession.to_dict = _atria_persist_to_dict
PaperSession.save = _atria_persist_save
PaperSession.from_dict = _atria_persist_from_dict
PaperSession.load = _atria_persist_load
PaperSession.execute_paper_trade = _atria_persist_execute_trade

# نام قدیمی و جدید باید به یک کلاس اشاره کنند.
PaperTradingSession = PaperSession
'''

    TARGET.write_text(text.rstrip() + "\n" + patch + "\n", encoding="utf-8")
    print("[PATCHED] Persistence compatibility به paper_session.py اضافه شد.")
else:
    print("[SKIP] این پچ قبلاً اضافه شده است.")

print("[CHECK] compileall...")
compile_result = subprocess.run(
    [sys.executable, "-m", "compileall", "-q", "src"],
    cwd=ROOT,
)

if compile_result.returncode != 0:
    print("[ROLLBACK] خطای Syntax؛ بازگردانی فایل...")
    shutil.copy2(BACKUP, TARGET)
    raise SystemExit(1)

print("[TEST-1] ابتدا فقط تست شکست‌خورده...")
one_test = subprocess.run(
    [
        sys.executable, "-m", "pytest", "-q",
        "tests/test_load_session.py",
        "--tb=short",
    ],
    cwd=ROOT,
)

if one_test.returncode != 0:
    print(f"[STOP] تست هدف شکست خورد. Backup محفوظ است: {BACKUP}")
    raise SystemExit(one_test.returncode)

print("[TEST-2] اجرای کامل تمام تست‌ها...")
all_tests = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "--tb=short"],
    cwd=ROOT,
)

raise SystemExit(all_tests.returncode)
