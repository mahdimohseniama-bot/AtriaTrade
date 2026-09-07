# -*- coding: utf-8 -*-
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# مسیردهی پویا برای Termux
WEB_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

from src.core.autopilot import AutoPilot  # noqa: E402

pilot = AutoPilot(initial_balance=1000.0, risk_pct=0.6, cooldown=10)

app = FastAPI(title="AtriaTrade Dashboard")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "status": "Paper Mode (Safe)"})


@app.post("/start")
async def start_pilot():
    ok = pilot.start()
    return {"started": ok, **pilot.status()}


@app.post("/stop")
async def stop_pilot():
    pilot.stop()
    return {"started": False, **pilot.status()}


@app.get("/status")
async def pilot_status():
    return pilot.status()
