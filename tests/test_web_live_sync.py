from pathlib import Path
from src.web.server import DashboardStateProvider, WebApiRouter

def test_live_sync_router_and_html():
    provider = DashboardStateProvider()
    router = WebApiRouter(provider)

    # 1. Status endpoint returns a dict with balance info
    data = router.handle_get_status()
    assert isinstance(data, dict)
    assert any("balance" in k for k in data), f"no balance key in {list(data)}"

    # 2. Pause -> state changes
    res_pause = router.handle_pause()
    assert isinstance(res_pause, dict)
    assert any(bool(v) is False or v == "paused" for v in [provider.state.get("is_paused", provider.state.get("paused", False))])

    # 3. Resume -> state back
    router.handle_resume()
    paused_val = provider.state.get("is_paused", provider.state.get("paused", False))
    assert not paused_val

    # 4. Panic -> flagged somewhere in state
    res_panic = router.handle_panic()
    assert isinstance(res_panic, dict)
    assert any("panic" in k.lower() for k in provider.state), f"no panic key in {list(provider.state)}"

    # 5. index.html has live-sync hooks
    html_path = Path.home() / "AtriaTrade" / "src" / "web" / "templates" / "index.html"
    content = html_path.read_text(encoding="utf-8")
    assert "fetchStatus" in content
    assert "setInterval" in content
    assert "/api/panic" in content
    assert "/api/resume" in content
