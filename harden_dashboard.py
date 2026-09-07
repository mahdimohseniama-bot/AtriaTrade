from pathlib import Path
from datetime import datetime
import shutil

# آدرس دقیق فایل
P = Path("src/web/static/js/dashboard.js")
assert P.exists(), f"فایل پیدا نشد! چک کن: {P.absolute()}"

# بکاپ‌گیری
backup = P.with_name(f"dashboard.js.bak_{datetime.now():%Y%m%d_%H%M%S}")
shutil.copy2(P, backup)
print(f"✔ بکاپ در مسیر {backup} ساخته شد.")

src = P.read_text(encoding="utf-8")

# --- ۱) پیاده‌سازی Exponential Backoff ---
if "pollWithBackoff" not in src:
    # حذف اینتروال قدیمی
    src = src.replace("setInterval(updateDashboard, 5000);", "")
    
    # اضافه کردن منطق جدید
    new_polling = """
// ==== Exponential Backoff Polling (Hardened) ====
let pollDelay = 1000;
const POLL_MAX = 30000;
async function pollWithBackoff() {
    if (navigator.onLine === false) {
        console.warn("[NET] offline — waiting...");
    } else {
        try {
            await updateDashboard();
            pollDelay = 1000; // موفقیت -> ریست به ۱ ثانیه
        } catch (e) {
            console.error("[POLL] failed:", e);
            pollDelay = Math.min(pollDelay * 2, POLL_MAX);
            console.warn(`[POLL] retry in ${pollDelay / 1000}s`);
        }
    }
    setTimeout(pollWithBackoff, pollDelay);
}
pollWithBackoff();
document.addEventListener("online",  () => { pollDelay = 1000; console.info("[NET] back online"); });
document.addEventListener("offline", () => console.warn("[NET] offline"));
"""
    src += new_polling
    print("✔ Exponential Backoff پیاده شد.")

# --- ۲) Safe Guards برای رندر ---
helpers = """
function safeDisplayValue(v, fallback = "—") {
    return (v === undefined || v === null || (typeof v === "number" && !isFinite(v))) ? fallback : v;
}
function safeLogValue(v) {
    if (v === undefined || v === null) return "[no data]";
    return typeof v === "object" ? JSON.stringify(v) : String(v);
}
"""
if "safeDisplayValue" not in src:
    # اضافه کردن به ابتدای فایل
    src = helpers + "\n" + src
    print("✔ Safe Guards اضافه شدند.")

P.write_text(src, encoding="utf-8")
print("✅ عملیات با موفقیت انجام شد!")
