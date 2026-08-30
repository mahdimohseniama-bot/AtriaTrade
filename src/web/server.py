import secrets
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os

app = FastAPI(title="AtriaTrade Web Console")

# مدیریت توکن‌های سشن ساده
ACTIVE_SESSIONS = set()
ADMIN_PASSWORD = "mehdi1234"

# تعریف مسیر تمپلیت‌ها
current_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

# وضعیت ماک سیستم برای تست اولیه
bot_status = {
    "is_running": False,
    "active_strategy": "SMC + Momentum Engine",
    "market": "BTC/USDT",
    "balance_usdt": 1000.0,
    "profit_reserve": 0.0,
    "current_pnl": 0.0,
    "trade_mode": "Paper Trading (Sandbox)",
    "logs": [
        "[SYSTEM] Security layer initialized.",
        "[AUTH] Console locked. Awaiting admin session."
    ]
}

def check_auth(request: Request):
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in ACTIVE_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    return True

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def handle_login(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        token = secrets.token_hex(16)
        ACTIVE_SESSIONS.add(token)
        bot_status["logs"].append("[AUTH] Admin successfully authenticated.")
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="session_token", value=token, httponly=True)
        return response
    else:
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "رمز عبور اشتباه است! دسترسی غیرمجاز ثبت شد."
        })

@app.get("/logout")
async def logout(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS.remove(session_token)
    response = RedirectResponse(url="/login")
    response.delete_cookie("session_token")
    return response

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, authenticated: bool = Depends(check_auth)):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "status": bot_status
    })

@app.get("/api/status")
async def get_status(authenticated: bool = Depends(check_auth)):
    return JSONResponse(content=bot_status)

@app.post("/api/bot/start")
async def start_bot(authenticated: bool = Depends(check_auth)):
    bot_status["is_running"] = True
    bot_status["logs"].append("[ENGINE] Bot execution started by Admin.")
    return {"status": "success", "message": "ربات فعال شد"}

@app.post("/api/bot/stop")
async def stop_bot(authenticated: bool = Depends(check_auth)):
    bot_status["is_running"] = False
    bot_status["logs"].append("[PANIC] Engine stopped immediately by Admin.")
    return {"status": "success", "message": "ربات متوقف شد"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
