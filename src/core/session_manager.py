import json
import uuid
from pathlib import Path
from datetime import datetime

from src.core.paper_session import PaperSession


class SessionManager:
    def __init__(self, storage_dir=None):
        if storage_dir is None:
            storage_dir = "data/paper_sessions"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create_new_session(self, initial_capital, session_name=None):
        if initial_capital <= 0:
            raise ValueError("Initial capital must be greater than zero.")

        session_id = str(uuid.uuid4())
        if session_name is None:
            session_name = f"paper_session_{session_id[:8]}"

        session = PaperSession(
            session_id=session_id,
            session_name=session_name,
            initial_capital=float(initial_capital),
        )

        self._save_session(session)
        return session

    def _session_path(self, session_id):
        return self.storage_dir / f"{session_id}.json"

    def _save_session(self, session):
        if not hasattr(session, "session_id"):
            raise AttributeError("PaperSession must have session_id.")

        data = self._session_to_dict(session)
        path = self._session_path(session.session_id)

        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def save_session(self, session):
        self._save_session(session)

    def load_session(self, session_id):
        path = self._session_path(session_id)

        if not path.exists():
            raise FileNotFoundError(f"Session file not found: {path}")

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return self._dict_to_session(data)

    def list_sessions(self):
        return sorted(self.storage_dir.glob("*.json"))

    def _session_to_dict(self, session):
        if hasattr(session, "to_dict"):
            return session.to_dict()

        data = {}
        for key, value in vars(session).items():
            if isinstance(value, datetime):
                value = value.isoformat()
            data[key] = value

        return data

    def _dict_to_session(self, data):
        session_id = data.get("session_id")
        session_name = data.get("session_name", f"session_{session_id[:8]}")
        initial_capital = data.get("initial_capital")

        if session_id is None:
            raise ValueError("Saved session has no session_id.")

        if initial_capital is None:
            raise ValueError("Saved session has no initial_capital.")

        session = PaperSession(
            session_id=session_id,
            session_name=session_name,
            initial_capital=float(initial_capital),
        )

        for key, value in data.items():
            if key in {"session_id", "session_name", "initial_capital"}:
                continue
            if hasattr(session, key):
                setattr(session, key, value)

        return session
