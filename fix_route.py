from pathlib import Path

server_path = Path.home() / "AtriaTrade" / "src" / "web" / "server.py"
print("Checking server file:", server_path.exists())
