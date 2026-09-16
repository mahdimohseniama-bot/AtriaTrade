import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path


class TradeJournal:
    """
    Persistent SQLite trade and event audit log manager for AtriaTrade.
    Records trades, system state changes, halts, and risk events.
    Supports persistent disk DB or persistent in-memory DB.
    """
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._is_memory = (db_path == ":memory:")
        self._memory_conn: Optional[sqlite3.Connection] = None

        if not self._is_memory:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        else:
            # Maintain an open connection for the lifetime of the in-memory journal
            self._memory_conn = sqlite3.connect(":memory:")
            self._memory_conn.row_factory = sqlite3.Row

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._is_memory and self._memory_conn is not None:
            return self._memory_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                order_type TEXT NOT NULL,
                price REAL NOT NULL,
                volume REAL NOT NULL,
                slippage_pct REAL,
                fee REAL,
                order_id TEXT,
                metadata TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT
            )
        """)
        conn.commit()
        if not self._is_memory:
            conn.close()

    def log_trade(
        self,
        symbol: str,
        side: str,
        order_type: str,
        price: float,
        volume: float,
        slippage_pct: float = 0.0,
        fee: float = 0.0,
        order_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Logs an executed or simulated trade."""
        if price <= 0 or volume <= 0:
            raise ValueError("Price and volume must be strictly positive")

        timestamp = datetime.now(timezone.utc).isoformat()
        meta_str = json.dumps(metadata or {})

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trade_logs (
                timestamp, symbol, side, order_type, price, volume, slippage_pct, fee, order_id, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, symbol.upper(), side.upper(), order_type.upper(), price, volume, slippage_pct, fee, order_id, meta_str))
        conn.commit()
        last_id = cursor.lastrowid
        if not self._is_memory:
            conn.close()
        return last_id

    def log_event(
        self,
        event_type: str,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> int:
        """Logs a system, risk, or operational event (e.g. Halt, Margin Alert)."""
        timestamp = datetime.now(timezone.utc).isoformat()
        details_str = json.dumps(details or {})

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO system_events (
                timestamp, event_type, severity, message, details
            ) VALUES (?, ?, ?, ?, ?)
        """, (timestamp, event_type.upper(), severity.upper(), message, details_str))
        conn.commit()
        last_id = cursor.lastrowid
        if not self._is_memory:
            conn.close()
        return last_id

    def get_trades(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent logged trades."""
        conn = self._get_connection()
        cursor = conn.cursor()
        if symbol:
            cursor.execute("""
                SELECT * FROM trade_logs WHERE symbol = ? ORDER BY id DESC LIMIT ?
            """, (symbol.upper(), limit))
        else:
            cursor.execute("""
                SELECT * FROM trade_logs ORDER BY id DESC LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        result = [
            {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "symbol": row["symbol"],
                "side": row["side"],
                "order_type": row["order_type"],
                "price": row["price"],
                "volume": row["volume"],
                "slippage_pct": row["slippage_pct"],
                "fee": row["fee"],
                "order_id": row["order_id"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }
            for row in rows
        ]
        if not self._is_memory:
            conn.close()
        return result

    def get_events(self, event_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent system events."""
        conn = self._get_connection()
        cursor = conn.cursor()
        if event_type:
            cursor.execute("""
                SELECT * FROM system_events WHERE event_type = ? ORDER BY id DESC LIMIT ?
            """, (event_type.upper(), limit))
        else:
            cursor.execute("""
                SELECT * FROM system_events ORDER BY id DESC LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        result = [
            {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "event_type": row["event_type"],
                "severity": row["severity"],
                "message": row["message"],
                "details": json.loads(row["details"]) if row["details"] else {}
            }
            for row in rows
        ]
        if not self._is_memory:
            conn.close()
        return result
