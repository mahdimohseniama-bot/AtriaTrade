import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# تعیین مسیر پایه‌ای پروژه
BASE_DIR = Path(__file__).resolve().parent.parent.parent
WEB_DIR = BASE_DIR / "src" / "web"
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

app = FastAPI(
    title="AtriaTrade Dashboard",
    description="Institutional-grade Trading Bot Interface",
    version="1.0.0"
)

# تنظیمات امنیتی و CORS (برای ارتباط راحت فرانت‌اند و بک‌اند)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# متصل کردن پوشه‌های فایل‌های ظاهری (CSS/JS) و قالب‌ها
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """رندر کردن صفحه اصلی داشبورد معاملاتی"""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "status": "Paper Mode (Safe)"}
    )

@app.get("/health")
async def health_check():
    """پایش سلامت سرور و ربات"""
    return {"status": "ok", "mode": "Paper Trading", "security": "No Real API Keys"}
