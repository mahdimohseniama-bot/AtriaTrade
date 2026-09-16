import pytest
from pathlib import Path

def test_dashboard_template_structure_and_assets():
    template_path = Path.home() / "AtriaTrade" / "src" / "web" / "templates" / "index.html"
    assert template_path.exists(), "index.html template must exist"

    content = template_path.read_text(encoding="utf-8")

    # Check HTML doctype and title
    assert "<!DOCTYPE html>" in content
    assert "AtriaTrade" in content
    assert "total-balance" in content
    assert "realized-pnl" in content
    assert "unrealized-pnl" in content
    assert "drawdown-val" in content

    # Check interactive controls & endpoints
    assert "togglePause" in content
    assert "triggerPanic" in content
    assert "btn-panic" in content
    assert "/api/pause" in content or "/api/status" in content
    assert "positions-tbody" in content
